from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi_project.dependencies import get_joke_service
from fastapi_project.main import create_app
from fastapi_project.models.base import Base
from fastapi_project.services.jokes import JokeService


@pytest.fixture(scope="session")
def postgres_url():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
async def engine(postgres_url):
    engine = create_async_engine(postgres_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:
    """Only one session for test, always with rollback."""
    conn = await engine.connect()
    trans = await conn.begin()
    sess = AsyncSession(
        bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    try:
        yield sess
    finally:
        await sess.close()
        await trans.rollback()
        await conn.close()


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
