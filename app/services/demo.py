from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.seed import DEMO_USERS

DEMO_USERS_BY_ID = {
    user["demo_id"]: user
    for user in DEMO_USERS
}


def resolve_demo_user(db: Session, demo_id: str) -> User | None:
    user_data = DEMO_USERS_BY_ID.get(demo_id)

    if user_data is None:
        return None

    user = db.scalar(
        select(User).where(User.email == user_data["email"])
    )

    if user is None or not user.is_active:
        return None

    return user