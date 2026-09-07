import datetime
import hashlib
import uuid
from datetime import UTC, timedelta
from typing import Any, Literal

import jwt
from pwdlib import PasswordHash

from fastapi_project.core.config import Settings

_password_hash = PasswordHash.recommended()

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return _password_hash.verify(password, hash)


def create_token(
    subject: uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    settings: Settings,
) -> str:
    now = datetime.now(UTC)
    payload: dict[dict, Any] = {
        "sub": str(subject),
        "type": str(token_type),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(
        payload, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(
    token: str, expected_type: TokenType, settings: Settings
) -> dict[str, Any]:
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
