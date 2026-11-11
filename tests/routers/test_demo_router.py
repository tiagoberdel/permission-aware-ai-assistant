import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db
from app.auth.jwt import decode_access_token
from app.models.user import User
from app.services.demo import DEMO_USERS_BY_ID

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

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    original_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides = original_overrides

def test_create_demo_session(client, demo_user):
    response = client.post(
        "/demo/sessions",
        json={"demo_user": "diego"},
    )

    assert response.status_code == 200
    data = response.json()

    token = data["access_token"]

    payload = decode_access_token(token)

    assert payload["session_type"] == "demo"
    assert payload["sub"] == str(demo_user.id)
    assert payload["conversation_id"] == data["conversation_id"]
    assert data["token_type"] == "bearer"

def test_unknown_demo_user(client):
    response = client.post(
        "/demo/sessions",
        json={"demo_user": "unknown"},
    )

    assert response.status_code == 404

def test_inactive_demo_user(client, db_session, demo_user):
    demo_user.is_active = False
    db_session.flush()

    response = client.post(
        "/demo/sessions",
        json={"demo_user": "diego"},
    )

    assert response.status_code == 404
    
def test_different_conversation_id_for_each_session(client, demo_user):
    response1 = client.post(
        "/demo/sessions",
        json={"demo_user": "diego"}
    )

    response2 = client.post(
        "/demo/sessions",
        json={"demo_user": "diego"}
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    token1 = data1["access_token"]
    token2 = data2["access_token"]

    payload1 = decode_access_token(token1)
    payload2 = decode_access_token(token2)

    assert payload1["conversation_id"] != payload2["conversation_id"]