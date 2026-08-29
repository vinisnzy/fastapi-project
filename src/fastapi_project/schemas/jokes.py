import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class JokeBase(BaseModel):
    setup: Annotated[str, Field(min_length=5, max_length=300)]
    punchline: Annotated[str, Field(min_length=1, max_length=100)]
    tag: Annotated[str, Field(min_length=1, max_length=50)]


class JokeCreate(JokeBase):
    pass


class JokeUpdate(BaseModel):
    setup: Annotated[str | None, Field(min_length=5, max_length=300)] = None
    punchline: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    tag: Annotated[str | None, Field(min_length=1, max_length=50)] = None


class JokeRead(JokeBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
