from pydantic import ConfigDict
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_project.models.base import Base, TimestampMixin, UUIDMixin


class Joke(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "jokes"

    setup: Mapped[str] = mapped_column(String(200), nullable=False)
    punchline: Mapped[str] = mapped_column(String(100), nullable=False)
    tag: Mapped[str] = mapped_column(String(50), nullable=False)

    model_config = ConfigDict(from_attributes=True)
