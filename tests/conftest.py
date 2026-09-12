import pytest

from fastapi_project.core.config import Settings

TEST_DATABASE_URL = "postgresql+asyncpg://x:x@localhost/x"
TEST_JWT_SECRET = "test-secret-key-with-32-bytes-min!!"


@pytest.fixture
def settings() -> Settings:
    """Settings for tests with fake env vars"""
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        DEBUG=False,
        JWT_SECRET=TEST_JWT_SECRET,
        ACCESS_TOKEN_EXPIRES_IN_MINUTES=15,
        REFRESH_TOKEN_EXPIRES_IN_DAYS=7,
    )
