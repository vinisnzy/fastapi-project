from random import choice

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate

from fastapi_project.repository.jokes import data
from fastapi_project.schemas.jokes import JokeCreate, JokeRead, JokeUpdate

router = APIRouter(prefix="/jokes", tags=["Jokes"])


@router.get("/", response_model=Page[JokeRead])
def get_jokes(tag: str | None = None) -> Page[JokeRead]:
    items = data if tag is None else [j for j in data if j["tag"] == tag]

    if tag is not None and not items:
        raise HTTPException(status_code=404, detail=f"No jokes with tag '{tag}'")
    return paginate(items)


@router.get("/random", response_model=JokeRead)
def get_random_joke(tag: str | None = None) -> JokeRead:
    pool = data if tag is None else [j for j in data if j["tag"] == tag]

    if not pool:
        raise HTTPException(status_code=404, detail=f"No jokes with tag '{tag}'")
    return JokeRead.model_validate(choice(pool))


@router.get("/{joke_id}", response_model=JokeRead)
def get_joke_by_id(joke_id: int) -> JokeRead:
    joke = next((j for j in data if j["id"] == joke_id), None)
    if joke is None:
        raise HTTPException(status_code=404, detail=f"Joke not found with id {joke_id}")
    return JokeRead.model_validate(data[joke_id])


@router.post("/", status_code=201, response_model=JokeRead)
def add_joke(joke: JokeCreate) -> JokeRead:
    new_joke = {
        "id": len(data),
        "setup": joke.setup,
        "punchline": joke.punchline,
        "tag": joke.tag,
    }
    data.append(new_joke)
    return JokeRead.model_validate(new_joke)


@router.patch("/{joke_id}", response_model=JokeRead)
def update_joke(joke_id: int, payload: JokeUpdate) -> JokeRead:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="There are no fields to update")

    joke = next((j for j in data if j["id"] == joke_id), None)
    if joke is None:
        raise HTTPException(status_code=404, detail=f"Joke not found with id {joke_id}")

    joke.update(
        {k: v for k, v in changes.items() if k in {"setup", "punchline", "tag"}}
    )
    return JokeRead.model_validate(joke)


@router.delete("/{joke_id}", status_code=204)
def delete_joke(joke_id: int) -> None:
    joke = next((j for j in data if j["id"] == joke_id), None)
    if joke is None:
        raise HTTPException(status_code=404, detail=f"Joke not found with id {joke_id}")
    data.remove(joke)
