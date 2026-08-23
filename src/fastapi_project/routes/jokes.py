from random import choice

from fastapi import APIRouter, HTTPException

from fastapi_project.repository.jokes import data
from fastapi_project.schemas.jokes import JokeCreate

router = APIRouter(prefix="/jokes", tags=["Jokes"])


@router.get("/")
def get_joke(tag: str | None = None) -> dict:
    if tag is not None:
        filtered: list[dict] = [j for j in data if j["tag"] == tag]

        if not filtered:
            raise HTTPException(status_code=404, detail=f"No jokes with tag '{tag}'")
        return choice(filtered)
    return choice(data)


@router.get("/{joke_id}")
def get_joke_by_id(joke_id: int) -> dict:
    if joke_id < 0 or joke_id >= len(data):
        raise HTTPException(status_code=404, detail=f"Joke not found with id {joke_id}")
    return data[joke_id]


@router.post("/")
def add_joke(joke: JokeCreate) -> dict:
    new_joke = {"setup": joke.setup, "punchline": joke.punchline, "tag": joke.tag}
    data.append(new_joke)
    return {"message": "Joke added!", "id": len(data) - 1, "joke": new_joke}
