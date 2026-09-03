from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.core.config import Settings
from fastapi_project.database.session import build_engine
from fastapi_project.models.base import Base


@pytest.fixture(scope="session")
def postgres_url():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
async def engine(postgres_url):
    engine = build_engine(Settings(DATABASE_URL=postgres_url, DEBUG=False))
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
