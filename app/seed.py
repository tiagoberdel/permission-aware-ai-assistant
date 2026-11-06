from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.roles import ROLE_DESCRIPTIONS

def seed_roles(db: Session) -> None:
    for role_name, description in ROLE_DESCRIPTIONS.items():
        existing_role = db.scalar(
            select(Role).where(Role.name == role_name.value)
        )

        if existing_role is None:
            db.add(
                Role(
                    name=role_name.value,
                    description=description
                )
            )
            
    db.commit()