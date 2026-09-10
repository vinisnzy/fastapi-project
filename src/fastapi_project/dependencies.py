from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.core.config import Settings
from fastapi_project.core.secret import decode_token
from fastapi_project.database.session import get_async_session
from fastapi_project.exceptions.exceptions import UnauthorizedError
from fastapi_project.models import User
from fastapi_project.repository.jokes import JokeRepository
from fastapi_project.repository.users import UserRepository
from fastapi_project.services.auth import AuthService
from fastapi_project.services.jokes import JokeService


def get_settings_from_state(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings_from_state)]

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def get_joke_repository(session: AsyncSessionDep) -> JokeRepository:
    return JokeRepository(session)


JokeRepositoryDep = Annotated[JokeRepository, Depends(get_joke_repository)]


def get_joke_service(repository: JokeRepositoryDep) -> JokeService:
    return JokeService(repository)


JokeServiceDep = Annotated[JokeService, Depends(get_joke_service)]


def get_user_repository(session: AsyncSessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_auth_service(
    repository: UserRepositoryDep, settings: SettingsDep
) -> AuthService:
    return AuthService(repository, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
TokenDep = Annotated[str | None, Depends(oauth2_scheme)]


async def get_current_user(
    token: TokenDep, repository: UserRepositoryDep, settings: SettingsDep
) -> User:
    if token is None:
        raise UnauthorizedError(message="Not authenticated")

    try:
        payload = decode_token(token, "access", settings)
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError(message="Token expired") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(message="Invalid token") from exc

    user = await repository.get_user_by_id(UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
