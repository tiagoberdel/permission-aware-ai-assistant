from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
import pytest

from app.auth.dependencies import (
    get_current_user,
    get_demo_user,
    get_token_payload,
)
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
    payload = get_token_payload(token)

    current_user = get_current_user(payload, db_session)

    assert current_user.id == user.id
    assert current_user.email == user.email

def test_get_current_user_nonexistent_user(db_session):
    token = create_access_token(uuid4())
    payload = get_token_payload(token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(payload, db_session)

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
    payload = get_token_payload(token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(payload, db_session)

    assert exc_info.value.status_code == 401

def test_get_token_payload_expired_token():
    token = create_access_token(
        uuid4(),
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_token_payload(token)

    assert exc_info.value.status_code == 401

def test_get_token_payload_invalid_token():
    token = "test-invalid-token"

    with pytest.raises(HTTPException) as exc_info:
        get_token_payload(token)

    assert exc_info.value.status_code == 401

def test_get_demo_user(db_session):
    user = User(
        id=uuid4(),
        email="demo@gmail.com",
        hashed_password="testpsw",
        first_name="Demo",
        last_name="User",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id, session_type="demo")
    payload = get_token_payload(token)

    demo_user = get_demo_user(
        payload,
        get_current_user(payload, db_session),
    )

    assert demo_user.id == user.id

def test_get_demo_user_rejects_normal_session(db_session):
    user = User(
        id=uuid4(),
        email="normal@gmail.com",
        hashed_password="testpsw",
        first_name="Normal",
        last_name="User",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id, session_type="normal")
    payload = get_token_payload(token)
    current_user = get_current_user(payload, db_session)

    with pytest.raises(HTTPException) as exc_info:
        get_demo_user(payload, current_user)

    assert exc_info.value.status_code == 403