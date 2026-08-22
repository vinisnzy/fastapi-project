from random import choice

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Joke(BaseModel):
    setup: str
    punchline: str
    tag: str


jokes: list[dict] = [
    {
        "setup": "Why do Python programmers prefer dark mode?",
        "punchline": "Because light attracts bugs.",
        "tag": "python",
    },
    {
        "setup": "What's the object-oriented way to become wealthy?",
        "punchline": "Inheritance.",
        "tag": "python",
    },
]


@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to the joke API!"}


@app.get("/joke")
def get_joke(tag: str | None) -> dict:
    if tag is not None:
        filtered: list[dict] = [j for j in jokes if j["tag"] == tag]

        if not filtered:
            raise HTTPException(status_code=404, detail=f"No jokes with tag '{tag}'")
        return choice(filtered)
    return choice(jokes)


@app.get("/joke/{joke_id}")
def get_joke_by_id(joke_id: int) -> dict:
    if joke_id < 0 or joke_id >= len(jokes):
        raise HTTPException(status_code=404, detail=f"Joke not found with id {joke_id}")
    return jokes[joke_id]


@app.post("/joke")
def add_joke(joke: Joke) -> dict:
    new_joke = {"setup": joke.setup, "punchline": joke.punchline, "tag": joke.tag}
    jokes.append(new_joke)
    return {
        "message": "Joke added!",
        "id": len(jokes) - 1,
        "joke": new_joke
    }
