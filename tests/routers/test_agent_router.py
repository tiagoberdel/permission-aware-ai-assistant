from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.routers.agent as agent_router
from app.auth.jwt import create_access_token
from app.db import get_db
from app.main import app
from app.models.user import User
from app.services.demo import DEMO_USERS_BY_ID

@pytest.fixture()
def demo_token(demo_user):
    conversation_id = uuid4()
    token = create_access_token(user_id=demo_user.id, session_type="demo", conversation_id=str(conversation_id))
    return {
        "access_token": token,
        "conversation_id": str(conversation_id),
    }

@pytest.fixture
def normal_token(demo_user):
    token = create_access_token(
        user_id=demo_user.id,
        session_type="normal",
    )
    return token

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

def test_ask_agent_success(client, demo_token, demo_user, monkeypatch):
    calls = []

    async def fake_ask_andino(query, user, conversation_id):
        calls.append((query, user, conversation_id))
        return "Información encontrada en los documentos."

    monkeypatch.setattr(
        agent_router,
        "ask_andino",
        fake_ask_andino,
    )

    response = client.post(
        "/agent/ask",
        json={"query": "Cuál es la política de vacaciones?"},
        headers={
            "Authorization": f"Bearer {demo_token['access_token']}"
        },
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "Información encontrada en los documentos."}
    assert len(calls) == 1

    query, user, conversation_id = calls[0]

    assert query == "Cuál es la política de vacaciones?"
    assert user is demo_user
    assert conversation_id == demo_token["conversation_id"]

def test_ask_agent_rejects_normal_session(client, normal_token):
    response = client.post(
        "/agent/ask",
        json={"query": "Cuál es la política de vacaciones?"},
        headers={
            "Authorization": f"Bearer {normal_token}"
        },
    )

    assert response.status_code == 403

def test_ask_agent_rejects_unauthenticated(client):
    response = client.post(
        "/agent/ask",
        json={"query": "Cuál es la política de vacaciones?"},
    )

    assert response.status_code == 401