import pytest

from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole

def test_create_user(db_session):
    user = User(
        email = "test@andino.com",
        hashed_password = "fake_password_hash",
        first_name = "Test",
        last_name = "User",
    )

    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert user.email == "test@andino.com"
    assert user.is_active is True
    assert user.created_at is not None

def test_user_email_must_be_unique(db_session):
    user1 = User(
        email = "dup@andino.com",
        hashed_password = "hash1",
        first_name = "dup1",
        last_name = "user1"
    )

    user2 = User(
            email = "dup@andino.com",
            hashed_password = "hash2",
            first_name = "dup2",
            last_name = "user2"
        )

    db_session.add(user1)
    db_session.flush()

    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()

def test_create_role(db_session):
    role = Role(
        name="employee",
        description="Base role assigned to every authenticated user"
    )

    db_session.add(role)
    db_session.flush()

    assert role.id is not None


def test_user_role_relationship(db_session):
    role = Role(
        name="sales",
        description="Sales department"
    )

    user = User(
        email = "test@andino.com",
        hashed_password = "testhashedpsw",
        first_name = "Test",
        last_name = "User"
    )

    relation = UserRole(
        user=user,
        role=role
    )

    db_session.add(relation)
    db_session.flush()

    assert relation.user_id == user.id
    assert relation.role_id == role.id

    saved_relation = db_session.get(
        UserRole,
        (user.id, role.id)
    )

    assert saved_relation is not None
    assert saved_relation.user.email == "test@andino.com"
    assert saved_relation.role.name == "sales"