import uuid

from fastapi_pagination import Page

from fastapi_project.exceptions.exceptions import NotFoundError
from fastapi_project.models.jokes import Joke
from fastapi_project.repository.jokes import IJokeRepository
from fastapi_project.schemas.jokes import JokeCreate, JokeUpdate


class JokeService:
    def __init__(self, repository: IJokeRepository) -> None:
        self.repository = repository

    async def get_jokes(self) -> Page[Joke]:
        return await self.repository.get_all_jokes()

    async def get_jokes_by_tag(self, tag: str) -> Page[Joke]:
        return await self.repository.get_jokes_by_tag(tag)

    async def get_random_joke(self, tag: str | None = None) -> Joke:
        joke = await self.repository.get_random_joke(tag)
        if joke is None:
            message = f"No jokes with tag '{tag}'" if tag else "No available jokes"
            raise NotFoundError(resource="Joke", message=message)
        return joke

    async def exists_joke_by_id(self, joke_id: uuid.UUID) -> bool:
        return bool(await self.repository.get_joke_by_id(joke_id))

    async def get_joke_by_id(self, joke_id: uuid.UUID) -> Joke:
        joke = await self.repository.get_joke_by_id(joke_id)
        if joke is None:
            raise NotFoundError("Joke", joke_id)
        return joke

    async def add_joke(self, joke: JokeCreate) -> Joke:
        return await self.repository.add_joke(joke.model_dump())

    async def update_joke(self, joke_id: uuid.UUID, payload: JokeUpdate) -> Joke:
        updatedJoke = await self.repository.update_joke(
            joke_id, payload.model_dump(exclude_unset=True)
        )
        if not updatedJoke:
            raise NotFoundError("Joke", joke_id)
        return updatedJoke

    async def delete_joke(self, joke_id: uuid.UUID) -> None:
        if not await self.repository.delete_joke(joke_id):
            raise NotFoundError("Joke", joke_id)
