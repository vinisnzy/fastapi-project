from random import choice

from fastapi import HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_project.repository.jokes import (
    IJokeRepository,
)
from fastapi_project.schemas.jokes import JokeCreate, JokeRead, JokeUpdate


class JokeService:
    def __init__(self, repository: IJokeRepository, session: AsyncSession) -> None:
        self.session = session
        self.repository = repository

    async def get_jokes(self) -> Page[JokeRead]:
        return paginate(
            [JokeRead.model_validate(j) for j in await self.repository.get_all_jokes()]
        )

    async def get_jokes_by_tag(self, tag: str) -> Page[JokeRead]:
        return paginate(
            [
                JokeRead.model_validate(j)
                for j in await self.repository.get_jokes_by_tag(tag)
            ]
        )

    async def get_random_joke(self, tag: str | None = None) -> JokeRead:
        if tag:
            pool = await self.repository.get_jokes_by_tag(tag)
            if not pool:
                raise HTTPException(
                    status_code=404, detail=f"No jokes with tag '{tag}'"
                )
        else:
            pool = await self.repository.get_all_jokes()
        return JokeRead.model_validate(choice(pool))

    async def exists_joke_by_id(self, joke_id: str) -> bool:
        joke = await self.get_joke_by_id(joke_id)
        return bool(joke)

    async def get_joke_by_id(self, joke_id: str) -> JokeRead:
        joke = await self.repository.get_joke_by_id(joke_id)
        if joke is None:
            raise HTTPException(
                status_code=404, detail=f"Joke not found with id {joke_id}"
            )
        return JokeRead.model_validate(joke)

    async def add_joke(self, joke: JokeCreate) -> JokeRead:
        return JokeRead.model_validate(await self.repository.add_joke(joke))

    async def update_joke(self, joke_id: str, payload: JokeUpdate) -> JokeRead:
        updatedJoke = await self.repository.update_joke(joke_id, payload)
        if not updatedJoke:
            raise HTTPException(
                status_code=404, detail=f"Joke not found with id {joke_id}"
            )
        return JokeRead.model_validate(updatedJoke)

    async def delete_joke(self, joke_id: str) -> None:
        if not await self.repository.delete_joke(joke_id):
            raise HTTPException(
                status_code=404, detail=f"Joke not found with id {joke_id}"
            )
