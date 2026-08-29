from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.database.session import get_async_session
from fastapi_project.repository.jokes import JokeRepository
from fastapi_project.services.jokes import JokeService

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def get_joke_repository(session: AsyncSessionDep) -> JokeRepository:
    return JokeRepository(session)


JokeRepositoryDep = Annotated[JokeRepository, Depends(get_joke_repository)]


def get_joke_service(
    session: AsyncSessionDep, repository: JokeRepositoryDep
) -> JokeService:
    return JokeService(repository, session)


JokeServiceDep = Annotated[JokeService, Depends(get_joke_service)]
