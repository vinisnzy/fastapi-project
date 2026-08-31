from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastapi_project.dependencies import get_joke_service
from fastapi_project.main import create_app
from fastapi_project.services.jokes import JokeService


@pytest.fixture
def joke_service() -> AsyncMock:
    return AsyncMock(spec=JokeService)


@pytest.fixture
async def app(joke_service: AsyncMock) -> AsyncIterator[FastAPI]:
    app = create_app()
    app.dependency_overrides[get_joke_service] = lambda: joke_service
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
