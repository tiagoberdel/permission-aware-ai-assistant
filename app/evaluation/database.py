from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models import User, UserRole
from app.roles import RoleName

def get_user_roles(email: str) -> list[RoleName]:
    with SessionLocal() as db:
        user = db.scalar(
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(UserRole.role)
            )
            .where(
                User.email == email,
                User.is_active == True,
                )
        )

        if user  is None:
            raise ValueError(
                f"Active user not found: {email}"
            )

        try:
            return [
                RoleName(user_role.role.name)
                for user_role in user.roles
            ]
        except ValueError as exc:
            raise ValueError(
                f"User {email} has an unknown role"
            ) from exc