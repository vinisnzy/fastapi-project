from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_project.core.config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(url=settings.DATABASE_URL, echo=settings.DEBUG)


def build_session_maker(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker[AsyncSession](engine, expire_on_commit=False)


async def get_async_session(request: Request) -> AsyncGenerator[AsyncSession]:
    async with request.app.state.session_maker() as session:
        yield session
