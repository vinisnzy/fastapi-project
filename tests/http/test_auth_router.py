import pytest
from tests.factories import make_user_model

from fastapi_project.exceptions.exceptions import ConflictError, UnauthorizedError
from fastapi_project.schemas.auth import TokenPair

VALID_PASSWORD = "valid-secret-password=123"


def token_pair() -> TokenPair:
    return TokenPair(access_token="access_token", refresh_token="refresh_token")


async def test_register_should_return_201(client, auth_service):
    user = make_user_model(email="user@example.com")
    auth_service.register.return_value = user

    response = await client.post(
        "/auth/register", json={"email": user.email, "password": VALID_PASSWORD}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == user.email
    assert body["role"] == user.role

    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_should_returns_409_when_email_is_taken(client, auth_service):
    auth_service.register.side_effect = ConflictError("Email already registered")

    response = await client.post(
        "/auth/register", json={"email": "user@example.com", "password": VALID_PASSWORD}
    )

    assert response.status_code == 409
    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"email": "user@example.com"},
        {"email": "not-an-email", "password": VALID_PASSWORD},
        {"email": "user@example.com", "password": "short"},
        {"email": "user@example.com", "password": "a" * 129},
    ],
    ids=[
        "empty",
        "missing_password",
        "invalid_email",
        "password_too_short",
        "password_too_long",
    ],
)
async def test_register_should_returns_422_with_invalid_payload(
    client, auth_service, payload
):
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    auth_service.register.assert_not_awaited()


async def test_login_should_returns_200(client, auth_service):
    auth_service.login.return_value = token_pair()
    response = await client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "access_token"
    assert body["refresh_token"] == "refresh_token"
    assert body["token_type"] == "bearer"
    auth_service.login.assert_awaited_once_with("user@example.com", VALID_PASSWORD)


async def test_login_should_returns_401_with_invalid_credentials(client, auth_service):
    auth_service.login.side_effect = UnauthorizedError()
    response = await client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_login_should_returns_422_without_form_fields(client, auth_service):
    response = await client.post("/auth/login", data={})
    assert response.status_code == 422
    auth_service.login.assert_not_awaited()


async def test_refresh_should_returns_200(client, auth_service):
    auth_service.refresh.return_value = token_pair()
    response = await client.post("/auth/refresh", json={"refresh_token": "old-refresh"})

    assert response.status_code == 200
    assert response.json()["access_token"] == "access_token"
    auth_service.refresh.assert_awaited_once_with("old-refresh")


async def test_refresh_should_returns_401_with_revoked_token(client, auth_service):
    auth_service.refresh.side_effect = UnauthorizedError(
        message="Refresh token revoked"
    )
    response = await client.post("/auth/refresh", json={"refresh_token": "reused"})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Refresh token revoked"


async def test_refresh_should_returns_422_without_token(client, auth_service):
    response = await client.post("/auth/refresh", json={})
    assert response.status_code == 422
    auth_service.refresh.assert_not_awaited()


async def test_logout_should_returns_204(client, auth_service):
    auth_service.logout.return_value = None

    response = await client.post("/auth/logout", json={"refresh_token": "refresh"})
    assert response.status_code == 204
    auth_service.logout.assert_awaited_once_with("refresh")


async def test_logout_should_returns_422_without_token(client, auth_service):
    response = await client.post("/auth/logout", json={})
    assert response.status_code == 422
    auth_service.logout.assert_not_awaited()


async def test_me_should_returns_200_when_authenticated(client, current_user):
    response = await client.get("/auth/me")

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(current_user.id)
    assert body["email"] == current_user.email
    assert "hashed_password" not in body


async def test_me_should_returns_401_when_not_authenticated(client, auth_state):
    auth_state["user"] = None

    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
