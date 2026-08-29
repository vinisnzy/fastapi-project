from fastapi import APIRouter
from fastapi_pagination import Page

from fastapi_project.dependencies import JokeServiceDep
from fastapi_project.schemas.jokes import JokeCreate, JokeRead, JokeUpdate

router = APIRouter(prefix="/jokes", tags=["Jokes"])


@router.get("/", response_model=Page[JokeRead])
async def get_jokes(service: JokeServiceDep) -> Page[JokeRead]:
    return await service.get_jokes()


@router.get("/random", response_model=JokeRead)
async def get_random_joke(service: JokeServiceDep, tag: str | None = None) -> JokeRead:
    return await service.get_random_joke(tag)


@router.get("/{joke_id}", response_model=JokeRead)
async def get_joke_by_id(service: JokeServiceDep, joke_id: str) -> JokeRead:
    return await service.get_joke_by_id(joke_id)


@router.post("/", status_code=201, response_model=JokeRead)
async def add_joke(service: JokeServiceDep, joke: JokeCreate) -> JokeRead:
    return await service.add_joke(joke)


@router.patch("/{joke_id}", response_model=JokeRead)
async def update_joke(
    service: JokeServiceDep, joke_id: str, payload: JokeUpdate
) -> JokeRead:
    return await service.update_joke(joke_id, payload)


@router.delete("/{joke_id}", status_code=204)
async def delete_joke(service: JokeServiceDep, joke_id: str) -> None:
    await service.delete_joke(joke_id)
