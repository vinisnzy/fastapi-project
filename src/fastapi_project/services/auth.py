from datetime import UTC, datetime, timedelta
from uuid import UUID

import anyio
import jwt

from fastapi_project.core.config import Settings
from fastapi_project.core.secret import (
    create_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from fastapi_project.exceptions.exceptions import ConflictError, UnauthorizedError
from fastapi_project.models import User
from fastapi_project.repository.users import IUserRepository
from fastapi_project.schemas.auth import TokenPair, UserCreate


class AuthService:
    def __init__(self, repository: IUserRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def register(self, payload: UserCreate) -> User:
        if await self.repository.get_user_by_email(payload.email):
            raise ConflictError(message="Email already registered")

        hash = await anyio.to_thread.run_sync(hash_password, payload.password)
        return await self.repository.add_user(
            {"email": payload.email, "hashed_password": hash}
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repository.get_user_by_email(email)

        if user is None:
            raise UnauthorizedError()

        valid = await anyio.to_thread.run_sync(
            verify_password, password, user.hashed_password
        )
        if not valid or not user.is_active:
            raise UnauthorizedError()

        return user

    async def issue_tokens(self, user: User) -> TokenPair:
        user_id = user.id
        access = create_token(
            user_id,
            "access",
            timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES),
            self.settings,
        )

        refresh_expires = timedelta(days=self.settings.REFRESH_TOKEN_EXPIRES_IN_DAYS)
        refresh = create_token(
            user_id,
            "refresh",
            refresh_expires,
            self.settings,
        )

        await self.repository.store_refresh_token(
            user_id=user_id,
            token_hash=hash_token(refresh),
            expires_at=datetime.now(UTC) + refresh_expires,
        )
        return TokenPair(access_token=access, refresh_token=refresh)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.authenticate(email, password)
        return await self.issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, "refresh", self.settings)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError(message="Invalid refresh token") from exc

        token_hash = hash_token(refresh_token)
        stored = await self.repository.get_active_refresh_token(token_hash)
        if stored is None:
            # Refresh token reuse detection
            self.repository.revoke_all_for_user(UUID(payload["sub"]))
            raise UnauthorizedError(message="Refresh token revoked")

        user = await self.repository.get_user_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError()

        await self.repository.revoke_refresh_token(token_hash)
        return await self.issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        await self.repository.revoke_refresh_token(hash_token(refresh_token))
