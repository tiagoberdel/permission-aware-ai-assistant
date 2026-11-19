from uuid import UUID

def build_thread_id(user_id: UUID | str, conversation_id: UUID | str) -> str:
    return f"user:{user_id}:conversation:{conversation_id}"