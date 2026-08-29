import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.models import Joke
from fastapi_project.schemas.jokes import JokeCreate, JokeRead, JokeUpdate


class IJokeRepository(ABC):
    @abstractmethod
    async def get_all_jokes(self) -> Sequence[JokeRead]:
        pass

    @abstractmethod
    async def get_jokes_by_tag(self, tag: str) -> Sequence[JokeRead]:
        pass

    @abstractmethod
    async def get_joke_by_id(self, joke_id: uuid.UUID) -> JokeRead | None:
        pass

    @abstractmethod
    async def add_joke(self, data: JokeCreate) -> JokeRead:
        pass

    @abstractmethod
    async def update_joke(
        self, joke_id: uuid.UUID, data: JokeUpdate
    ) -> JokeRead | None:
        pass

    @abstractmethod
    async def delete_joke(self, joke_id: uuid.UUID) -> bool:
        pass


class JokeRepository(IJokeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_jokes(self) -> Sequence[JokeRead]:
        result = await self.session.execute(select(Joke))
        return [JokeRead.model_validate(joke) for joke in result.scalars().all()]

    async def get_jokes_by_tag(self, tag: str) -> Sequence[JokeRead]:
        result = await self.session.execute(select(Joke).where(Joke.tag == tag))
        return [JokeRead.model_validate(joke) for joke in result.scalars().all()]

    async def get_joke_by_id(self, joke_id: uuid.UUID) -> JokeRead | None:
        result = await self.session.execute(select(Joke).where(Joke.id == joke_id))
        return JokeRead.model_validate(result.scalar_one_or_none())

    async def add_joke(self, data: JokeCreate) -> JokeRead:
        joke = Joke(**data.model_dump())
        self.session.add(joke)
        await self.session.commit()
        return JokeRead.model_validate(joke)

    async def update_joke(
        self, joke_id: uuid.UUID, data: JokeUpdate
    ) -> JokeRead | None:
        setted_data = data.model_dump(exclude_unset=True)

        if setted_data:
            await self.session.execute(
                update(Joke).where(Joke.id == joke_id).values(**setted_data)
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
