from collections.abc import Sequence
from typing import Any
from uuid import UUID

from fastapi_project.models.jokes import Joke
from fastapi_project.repository.jokes import IJokeRepository


class FakeJokeRepository(IJokeRepository):
    def __init__(self, initials: list[dict[str, Any]] | None = None) -> None:
        self.items: dict[UUID, dict[str, Any]] = {j["id"]: j for j in (initials or [])}

    async def get_all_jokes(self) -> Sequence[Joke]:
        return [Joke(**j) for j in self.items.values()]

    async def get_jokes_by_tag(self, tag: str) -> Sequence[Joke]:
        return [Joke(**j) for j in self.items.values() if j["tag"] == tag]

    async def get_joke_by_id(self, joke_id: UUID) -> Joke | None:
        joke = self.items.get(joke_id)
        return Joke(**joke) if joke is not None else None

    async def add_joke(self, data: dict[str, Any]) -> Joke:
        self.items[data["id"]] = data
        return Joke(**data)

    async def update_joke(self, joke_id: UUID, data: dict[str, Any]) -> Joke | None:
        if data:
            self.items[joke_id] = data

        return await self.get_joke_by_id(joke_id)

    async def delete_joke(self, joke_id: UUID) -> bool:
        joke = self.get_joke_by_id(joke_id)

        if not joke:
            return False

        del self.items[joke_id]
        return True
