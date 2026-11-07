from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
import pytest

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.models.user import User

def test_get_current_user(db_session):
    user = User(
        id=uuid4(),
        email="test@gmail.com",
        hashed_password="testpsw",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)

    current_user = get_current_user(token, db_session)

    assert current_user.id == user.id
    assert current_user.email == user.email

def test_get_current_user_token_expired(db_session):
    token = create_access_token(
        uuid4(),
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, db_session)

    assert exc_info.value.status_code == 401

def test_get_current_user_nonexistent_user(db_session):
    token = create_access_token(uuid4())

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, db_session)

    assert exc_info.value.status_code == 401

def test_get_current_user_inactive_user(db_session):
    user = User(
            id=uuid4(),
            email="test@gmail.com",
            hashed_password="testpsw",
            first_name="Test",
            last_name="User",
            is_active=False,
        )
    
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, db_session)

    assert exc_info.value.status_code == 401

def test_get_current_user_invalid_token(db_session):
    token = "test-invalid-token"

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, db_session)

    assert exc_info.value.status_code == 401