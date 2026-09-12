from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi_project.models import RefreshToken, User
from fastapi_project.models.jokes import Joke
from fastapi_project.repository.jokes import IJokeRepository
from fastapi_project.repository.users import IUserRepository


class FakeJokeRepository(IJokeRepository):
    def __init__(self, initials: list[dict[str, Any]] | None = None) -> None:
        self.items: dict[UUID, dict[str, Any]] = {}
        for j in initials or []:
            jid = j.get("id") or uuid4()
            self.items[jid] = {**j, "id": jid}

    async def get_all_jokes(self) -> Sequence[Joke]:
        return [Joke(**j) for j in self.items.values()]

    async def get_jokes_by_tag(self, tag: str) -> Sequence[Joke]:
        return [Joke(**j) for j in self.items.values() if j["tag"] == tag]

    async def get_joke_by_id(self, joke_id: UUID) -> Joke | None:
        joke = self.items.get(joke_id)
        return Joke(**joke) if joke is not None else None

    async def add_joke(self, data: dict[str, Any]) -> Joke:
        jid = data.get("id") or uuid4()
        item = {**data, "id": jid}
        self.items[jid] = item
        return Joke(**item)

    async def update_joke(self, joke_id: UUID, data: dict[str, Any]) -> Joke | None:
        item = self.items.get(joke_id)
        if item is None:
            return None

        self.items[joke_id] = {**item, **data, "id": joke_id}
        return await self.get_joke_by_id(joke_id)

    async def delete_joke(self, joke_id: UUID) -> bool:
        joke = await self.get_joke_by_id(joke_id)

        if not joke:
            return False

        del self.items[joke_id]
        return True


class FakeUserRepository(IUserRepository):
    def __init__(self, initials: list[dict[str, Any]] | None = None) -> None:
        self.users: dict[UUID, dict[str, Any]] = {}
        self.tokens: dict[str, dict[str, Any]] = {}
        for u in initials or []:
            uid = u.get("id") or uuid4()
            self.users[uid] = {"role": "users", "is_active": True, **u, "id": uid}

    async def get_user_by_email(self, email: str) -> User | None:
        for u in self.users.values():
            if u["email"] == email:
                return User(**u)
        return None

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        user = self.users.get(user_id)
        return User(**user) if user is not None else None

    async def add_user(self, data: dict[str, Any]) -> User:
        uid = data.get("id") or uuid4()
        item = {"role": "users", "is_active": True, **data, "id": uid}
        self.users[uid] = item
        return User(**item)

    async def update_user(self, user_id: UUID, data: dict[str, Any]) -> User | None:
        item = self.users.get(user_id)
        if item is None:
            return None

        self.users[user_id] = {**item, **data, "id": user_id}
        return await self.get_user_by_id(user_id)

    async def store_refresh_token(
        self, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        item = dict(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.tokens[token_hash] = item
        return RefreshToken(**item)

    async def get_active_refresh_token(self, token_hash: str) -> RefreshToken:
        item = self.tokens.get(token_hash)
        if (
            item is None
            or item["revoked_at"] is not None
            or item["expires_at"] <= datetime.now(UTC)
        ):
            return None
        return RefreshToken(**item)

    async def revoke_refresh_token(self, token_hash: str) -> None:
        for item in self.tokens.values():
            item = self.tokens.get(token_hash)
            if item is not None:
                item["revoked_at"] = datetime.now(UTC)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for item in self.tokens.values():
            if item["user_id"] == user_id and item["revoked_at"] is None:
                item["revoked_at"] = datetime.now(UTC)
