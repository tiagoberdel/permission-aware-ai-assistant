from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.config import settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
    session_type: str = "normal",
    conversation_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + expires_delta,
        "session_type": session_type,
    }

    if conversation_id is not None:
        payload["conversation_id"] = conversation_id

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALGORITHM,
    )

    return token


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],
    )

    return payload