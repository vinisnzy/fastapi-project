import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.models import Joke


class IJokeRepository(ABC):
    @abstractmethod
    async def get_all_jokes(self) -> Sequence[Joke]:
        pass

    @abstractmethod
    async def get_jokes_by_tag(self, tag: str) -> Sequence[Joke]:
        pass

    @abstractmethod
    async def get_joke_by_id(self, joke_id: uuid.UUID) -> Joke | None:
        pass

    @abstractmethod
    async def add_joke(self, data: dict[str, Any]) -> Joke:
        pass

    @abstractmethod
    async def update_joke(
        self, joke_id: uuid.UUID, data: dict[str, Any]
    ) -> Joke | None:
        pass

    @abstractmethod
    async def delete_joke(self, joke_id: uuid.UUID) -> bool:
        pass


class JokeRepository(IJokeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_jokes(self) -> Sequence[Joke]:
        result = await self.session.execute(select(Joke))
        return result.scalars().all()

    async def get_jokes_by_tag(self, tag: str) -> Sequence[Joke]:
        result = await self.session.execute(select(Joke).where(Joke.tag == tag))
        return result.scalars().all()

    async def get_joke_by_id(self, joke_id: uuid.UUID) -> Joke | None:
        result = await self.session.execute(select(Joke).where(Joke.id == joke_id))
        return result.scalar_one_or_none()

    async def add_joke(self, data: dict[str, Any]) -> Joke:
        joke = Joke(**data)
        self.session.add(joke)
        await self.session.commit()
        return joke

    async def update_joke(
        self, joke_id: uuid.UUID, data: dict[str, Any]
    ) -> Joke | None:
        if data:
            await self.session.execute(
                update(Joke).where(Joke.id == joke_id).values(**data)
            )
            await self.session.commit()

        return await self.get_joke_by_id(joke_id)

    async def delete_joke(self, joke_id: uuid.UUID) -> bool:
        result = await self.session.execute(select(Joke).where(Joke.id == joke_id))
        joke = result.scalar_one_or_none()

        if not joke:
            return False

        await self.session.delete(joke)
        await self.session.commit()
        return True


def get_joke_repository(session: AsyncSession):
    return JokeRepository(session)
