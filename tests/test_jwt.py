from datetime import timedelta
from uuid import uuid4

import jwt
import pytest

from app.auth.jwt import create_access_token, decode_access_token


def test_create_access_token():
    user_id = uuid4()

    token = create_access_token(user_id)

    assert isinstance(token, str)


def test_decode_access_token():
    user_id = uuid4()

    token = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] - payload["iat"] == 30 * 60


def test_expired_token():
    user_id = uuid4()

    token = create_access_token(
        user_id,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_changed_token():
    user_id = uuid4()

    token = create_access_token(user_id)

    token_without_signature = token.rsplit(".", 1)[0]
    manipulated_token = token_without_signature + ".invalidsignature"

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(manipulated_token)


def test_wrong_token_format():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("this-is-not-a-valid-jwt")