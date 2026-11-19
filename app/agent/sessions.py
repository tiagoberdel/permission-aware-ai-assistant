
from uuid import UUID
from dataclasses import dataclass
from threading import Lock
from time import monotonic

from app.agent.graph import checkpointer
from app.agent.threads import build_thread_id


SESSION_TTL_SECONDS = 10 * 60
MAX_ACTIVE_SESSIONS = 200


class SessionLimitReached(Exception):
    pass

class SessionExpired(Exception):
    pass


@dataclass
class ActiveSession:
    user_id: UUID
    thread_id: str
    last_seen: float


active_sessions: dict[str, ActiveSession] = {}

sessions_lock = Lock()


def _purge_expired_locked(now: float) -> int:
    expired_keys = []

    for key, session in active_sessions.items():
        if now - session.last_seen >= SESSION_TTL_SECONDS:
            expired_keys.append(key)

    for key in expired_keys:
        session = active_sessions[key]
        del active_sessions[key]
        checkpointer.delete_thread(session.thread_id)

    return len(expired_keys)


def purge_expired() -> int:
    with sessions_lock:
        return _purge_expired_locked(monotonic())


def register(user_id: UUID, conversation_id: UUID | str) -> str:
    thread_id = build_thread_id(user_id, conversation_id)
    conversation_key = str(conversation_id)

    with sessions_lock:
        actual_time = monotonic()

        _purge_expired_locked(actual_time)

        if conversation_key in active_sessions:
            session = active_sessions[conversation_key]

            if session.user_id == user_id:
                session.last_seen = actual_time
                return session.thread_id

            raise ValueError("Conversation ID already belongs to another user.")

        if len(active_sessions) >= MAX_ACTIVE_SESSIONS:
            raise SessionLimitReached()

        session = ActiveSession(
            user_id=user_id,
            thread_id=thread_id,
            last_seen=actual_time,
        )

        active_sessions[conversation_key] = session

        return thread_id

def touch(user_id: UUID, conversation_id: UUID | str) -> str:
    conversation_key = str(conversation_id)

    with sessions_lock:
        actual_time = monotonic()
        session = active_sessions.get(conversation_key)

        if session is None or session.user_id != user_id:
            raise SessionExpired()

        if actual_time - session.last_seen >= SESSION_TTL_SECONDS:
            del active_sessions[conversation_key]
            checkpointer.delete_thread(session.thread_id)
            raise SessionExpired()

        session.last_seen = actual_time

        return session.thread_id