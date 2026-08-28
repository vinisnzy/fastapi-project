from abc import ABC, abstractmethod
from collections.abc import Sequence

from fastapi_project.schemas.jokes import JokeCreate, JokeRead, JokeUpdate


class IJokeRepository(ABC):
    @abstractmethod
    async def get_all_jokes(self) -> Sequence[JokeRead]:
        pass

    @abstractmethod
    async def get_jokes_by_tag(self, tag: str) -> Sequence[JokeRead]:
        pass

    @abstractmethod
    async def get_joke_by_id(self, joke_id: str) -> JokeRead | None:
        pass

    @abstractmethod
    async def add_joke(self, data: JokeCreate) -> JokeRead:
        pass

    @abstractmethod
    async def update_joke(self, joke_id: str, data: JokeUpdate) -> JokeRead | None:
        pass

    @abstractmethod
    async def delete_joke(self, joke_id: str) -> bool:
        pass
