
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.db import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.roles import ROLE_DESCRIPTIONS


DEMO_USERS = [
    {
        "email": "sofia@andino.com",
        "password": "demo-password",
        "first_name": "Sofía",
        "last_name": "Gómez",
        "job_title": "Sales Representative",
        "is_visitor": False,
        "roles": ["employee", "sales"],
    },
    {
        "email": "ramon@andino.com",
        "password": "demo-password",
        "first_name": "Ramón",
        "last_name": "Rodríguez",
        "job_title": "Chief Executive Officer",
        "is_visitor": False,
        "roles": ["employee", "sales", "finance", "hr"],
    },
    {
        "email": "martin@andino.com",
        "password": "demo-password",
        "first_name": "Martín",
        "last_name": "Pérez",
        "job_title": "Finance Analyst",
        "is_visitor": False,
        "roles": ["employee", "finance"],
    },
    {
        "email": "laura@andino.com",
        "password": "demo-password",
        "first_name": "Laura",
        "last_name": "Fernández",
        "job_title": "HR Manager",
        "is_visitor": False,
        "roles": ["employee", "hr"],
    },
    {
        "email": "diego@andino.com",
        "password": "demo-password",
        "first_name": "Diego",
        "last_name": "Martínez",
        "job_title": "Sales Manager",
        "is_visitor": False,
        "roles": ["employee", "sales"],
    },
    {
        "email": "valentina@andino.com",
        "password": "demo-password",
        "first_name": "Valentina",
        "last_name": "Silva",
        "job_title": "Finance Manager",
        "is_visitor": False,
        "roles": ["employee", "finance"],
    },
    {
        "email": "visitor@andino.com",
        "password": "demo-password",
        "first_name": "Visitor",
        "last_name": "Andino",
        "job_title": "External Visitor",
        "is_visitor": True,
        "roles": [],
    },
]


def seed_roles(db: Session) -> None:
    for role_name, description in ROLE_DESCRIPTIONS.items():
        existing_role = db.scalar(
            select(Role).where(Role.name == role_name.value)
        )

        if existing_role is None:
            db.add(
                Role(
                    name=role_name.value,
                    description=description,
                )
            )

    db.commit()


def seed_demo_users(db: Session) -> None:
    for user_data in DEMO_USERS:
        existing_user = db.scalar(
            select(User).where(
                User.email == user_data["email"]
            )
        )

        if existing_user is not None:
            continue

        roles = db.scalars(
            select(Role).where(
                Role.name.in_(user_data["roles"])
            )
        ).all()

        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            job_title=user_data["job_title"],
            is_visitor=user_data["is_visitor"],
            roles=[
                UserRole(role=role)
                for role in roles
            ],
        )

        db.add(user)

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_roles(db)
        seed_demo_users(db)

    print("Andino demo data seeded successfully.")


if __name__ == "__main__":
    main()
