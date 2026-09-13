from datetime import timedelta

import pytest
from tests.factories import make_dict_user
from tests.fake import FakeUserRepository

from fastapi_project.core.secret import create_token
from fastapi_project.dependencies import get_current_user
from fastapi_project.exceptions.exceptions import UnauthorizedError


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository(initials=[make_dict_user(email="user@email.com")])


@pytest.fixture
def user_id(repository: FakeUserRepository):
    return next(iter(repository.users))


async def test_should_return_current_user_with_valid_access_token(
    repository, user_id, settings
):
    token = create_token(user_id, "access", timedelta(minutes=15), settings)

    user = await get_current_user(token, repository, settings)

    assert user.id == user_id
    assert user.email == "user@email.com"


async def test_should_raise_error_when_token_is_missing(repository, settings):
    with pytest.raises(UnauthorizedError) as exc:
        await get_current_user(None, repository, settings)
    assert "Not authenticated" in str(exc.value)


async def test_should_raise_error_when_token_is_expired(repository, user_id, settings):
    expired_token = create_token(user_id, "access", timedelta(minutes=-1), settings)
    with pytest.raises(UnauthorizedError) as exc:
        await get_current_user(expired_token, repository, settings)
    assert "Token expired" in str(exc.value)


async def test_should_raise_error_when_refresh_token_is_used_as_access(
    repository, user_id, settings
):
    refresh_token = create_token(user_id, "refresh", timedelta(days=7), settings)
    with pytest.raises(UnauthorizedError) as exc:
        await get_current_user(refresh_token, repository, settings)
    assert "Invalid token" in str(exc.value)


async def test_should_raise_error_when_user_no_longer_exists(repository, settings):
    from uuid import uuid4

    token = create_token(uuid4(), "access", timedelta(minutes=15), settings)
    with pytest.raises(UnauthorizedError) as exc:
        await get_current_user(token, repository, settings)

    assert "Invalid credentials" in str(exc.value)


async def test_should_raise_error_when_user_is_inactive(repository, user_id, settings):
    await repository.update_user(user_id, {"is_active": False})
    token = create_token(user_id, "access", timedelta(minutes=15), settings)
    with pytest.raises(UnauthorizedError) as exc:
        await get_current_user(token, repository, settings)
    assert "Invalid credentials" in str(exc.value)
