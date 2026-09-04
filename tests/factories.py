from typing import Any
from uuid import uuid4

from fastapi_project.models.jokes import Joke


def make_joke_model(**overrides) -> Joke:
    data = dict(
        id=uuid4(),
        setup="Why do Python programmers prefer dark mode?",
        punchline="Because light attracts bugs.",
        tag="python",
    )
    return Joke(**{**data, **overrides})


def make_dict_joke(**overrides) -> dict[str, Any]:
    data = dict(
        setup="Why do Python programmers prefer dark mode?",
        punchline="Because light attracts bugs.",
        tag="python",
    )
    return {**data, **overrides}
