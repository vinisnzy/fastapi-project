import datetime
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.models import RefreshToken, User


class IUserRepository(ABC):
    @abstractmethod
    async def get_user_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def add_user(self, data: dict[str, Any]) -> User: ...

    @abstractmethod
    async def update_user(self, user_id: UUID, data: dict[str, Any]) -> User | None: ...

    @abstractmethod
    async def store_refresh_token(
        self, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken: ...

    @abstractmethod
    async def get_active_refresh_token(self, token_hash: str) -> RefreshToken: ...

    @abstractmethod
    async def revoke_refresh_token(self, token_hash: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None: ...


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_user(self, data: dict[str, Any]) -> User:
        user = User(**data)
        self.session.add(user)
        await self.session.commit()
        return user

    async def update_user(self, user_id: UUID, data: dict[str, Any]) -> User | None:
        if data:
            await self.session.execute(
                update(User).where(User.id == user_id).values(**data)
            )
            await self.session.commit()
        return await self.get_user_by_id(user_id)

    async def store_refresh_token(
        self, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.session.add(token)
        await self.session.commit()
        return token

    async def get_active_refresh_token(self, token_hash: str) -> RefreshToken:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(datetime.UTC),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
            )
            .values(revoked_at=datetime.now(datetime.UTC))
        )
        await self.session.commit()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(datetime.UTC))
        )
        await self.session.commit()
