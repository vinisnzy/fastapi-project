from typing import Any
from uuid import uuid4

from fastapi_project.models import User
from fastapi_project.models.jokes import Joke


def make_dict_joke(**overrides) -> dict[str, Any]:
    data = dict(
        setup="Why do Python programmers prefer dark mode?",
        punchline="Because light attracts bugs.",
        tag="python",
    )
    return {**data, **overrides}


def make_joke_model(**overrides) -> Joke:
    return Joke(**make_dict_joke(**overrides))


def make_dict_user(**overrides) -> dict[str, Any]:
    data = dict(
        id=uuid4(),
        email=f"user-{uuid4().hex[:8]}@email.com",
        hashed_password="$argon2-fake-hash",
        role="users",
        is_active=True,
    )
    return {**data, **overrides}


def make_user_model(**overrides) -> User:
    return User(**make_dict_user(**overrides))
