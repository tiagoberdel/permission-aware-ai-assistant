from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.auth.passwords import verify_password

DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$i7CZjzGuEUfG2zt4jZ/Fvw$RC6tgiJ9mdam//NFYw1FTC08beqiaIr4DZu0BdkkBhE"

def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        verify_password(password, DUMMY_HASH)
        return None

    password_valid = verify_password(
        password,
        user.hashed_password,
    )

    if not password_valid or not user.is_active:
        return None

    return user
