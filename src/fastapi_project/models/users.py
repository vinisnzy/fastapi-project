from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_project.models import Base
from fastapi_project.models.base import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="users")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
