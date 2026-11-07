import pytest
from unittest.mock import patch

from app.services.auth import DUMMY_HASH
from app.models.user import User
from app.services.auth import authenticate_user
from app.auth.passwords import hash_password

@pytest.fixture
def test_user(db_session):
    password = "test-password"

    user = User(
        email="test@gmail.com",
        hashed_password=hash_password(password),
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user

def test_authenticate_user_success(db_session, test_user):
    authenticated_user = authenticate_user(
        db_session,
        test_user.email,
        "test-password",
    )

    assert authenticated_user == test_user

def test_authenticate_user_invalid_password(db_session, test_user):
    authenticated_user = authenticate_user(
        db_session,
        test_user.email,
        "not-the-password",
    )

    assert authenticated_user is None

def test_authenticate_user_inexistent(db_session):
    authenticated_user = authenticate_user(
        db_session,
        "nonexistent@gmail.com",
        "test-password",
    )

    assert authenticated_user is None

def test_authenticate_user_inactive(db_session, test_user):
    test_user.is_active = False
    db_session.commit()

    authenticated_user = authenticate_user(
        db_session,
        test_user.email,
        "test-password",
    )

    assert authenticated_user is None

def test_authenticate_inexistent_user_dummy_hash(db_session):
    with patch(
        "app.services.auth.verify_password",
        return_value=False,
    ) as mock_verify:

        authenticated_user = authenticate_user(
            db_session,
            "inexistent@gmail.com",
            "test-password",
        )

    assert authenticated_user is None

    mock_verify.assert_called_once_with(
        "test-password",
        DUMMY_HASH,
    )