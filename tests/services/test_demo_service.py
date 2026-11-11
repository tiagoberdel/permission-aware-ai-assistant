import pytest

from app.models.user import User
from app.services.demo import DEMO_USERS_BY_ID, resolve_demo_user

@pytest.fixture
def demo_user(db_session):
    user_data = DEMO_USERS_BY_ID["diego"]

    user = User(
        email=user_data["email"],
        hashed_password="test-hash",
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user

def test_resolve_demo_user(db_session, demo_user):
    user_id = "diego"

    user = resolve_demo_user(db_session, user_id)

    assert user is not None
    assert user.email == demo_user.email

def test_resolve_unknown_demo_user(db_session):
    user_id = "unknown"

    user = resolve_demo_user(db_session, user_id)

    assert user is None

def test_user_not_in_db(db_session):
    user_id = "diego"

    user = resolve_demo_user(db_session, user_id)

    assert user is None

def test_user_inactive(db_session, demo_user):
    user_id = "diego"

    demo_user.is_active = False
    db_session.commit()

    user = resolve_demo_user(db_session, user_id)

    assert user is None