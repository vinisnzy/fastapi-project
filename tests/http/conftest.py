from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from tests.factories import make_user_model

from fastapi_project.core.config import Settings
from fastapi_project.dependencies import (
    get_auth_service,
    get_current_user,
    get_joke_service,
)
from fastapi_project.exceptions.exceptions import UnauthorizedError
from fastapi_project.main import create_app
from fastapi_project.models import User
from fastapi_project.services.auth import AuthService
from fastapi_project.services.jokes import JokeService


@pytest.fixture
def joke_service() -> AsyncMock:
    return AsyncMock(spec=JokeService)


@pytest.fixture
def auth_service() -> AsyncMock:
    return AsyncMock(spec=AuthService)


@pytest.fixture
def current_user() -> User:
    return make_user_model(email="user@email.com")


@pytest.fixture
def auth_state(current_user: User) -> dict[str, Any]:
    """Control the authenticated user, put None to simulate 401"""
    return {"user": current_user}


@pytest.fixture
async def app(
    settings: Settings,
    joke_service: AsyncMock,
    auth_service: AsyncMock,
    auth_state: dict[str, Any],
) -> AsyncIterator[FastAPI]:
    app = create_app(settings)

    def _current_user() -> User:
        user = auth_state["user"]
        if user is None:
            raise UnauthorizedError(message="Not authenticated")
        return user

    app.dependency_overrides[get_joke_service] = lambda: joke_service
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_current_user] = _current_user
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
