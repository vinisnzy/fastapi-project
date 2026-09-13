from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from tests.factories import make_dict_user

from fastapi_project.repository.users import UserRepository


@pytest.fixture
def repository(session):
    return UserRepository(session)


def token_hash(prefix: str = "hash") -> str:
    return f"{prefix}-{uuid4().hex}"


async def test_should_add_user_and_return_user_by_id(repository):
    added = await repository.add_user(make_dict_user())

    found = await repository.get_user_by_id(added.id)

    assert found is not None
    assert found.id == added.id
    assert found.email == added.email


async def test_should_return_user_by_email(repository):
    added = await repository.add_user(make_dict_user(email="user@email.com"))
    found = await repository.get_user_by_email("user@email.com")

    assert found is not None
    assert found.id == added.id


async def test_should_return_none_if_user_not_exists_by_email(repository):
    assert await repository.get_user_by_email("ghost@example.com") is None


async def test_should_return_none_if_user_not_exists_by_id(repository):
    assert await repository.get_user_by_id(uuid4()) is None


async def test_should_apply_column_defaults_on_add_user(repository):
    added = await repository.add_user(
        {"email": "defaults@example.com", "hashed_password": "hash"}
    )

    found = await repository.get_user_by_id(added.id)

    assert found.role == "users"
    assert found.is_active is True


async def test_should_not_allow_duplicated_email(repository):
    await repository.add_user(make_dict_user(email="dup@example.com"))
    with pytest.raises(IntegrityError):
        await repository.add_user(make_dict_user(email="dup@example.com"))


async def test_should_update_user(repository):
    added = await repository.add_user(make_dict_user())

    updated = await repository.update_user(added.id, {"is_active": False})

    assert updated is not None
    assert updated.id == added.id
    assert updated.is_active is False


async def test_should_return_user_unchanged_when_update_data_is_empty(repository):
    added = await repository.add_user(make_dict_user())

    updated = await repository.update_user(added.id, {})

    assert updated is not None
    assert updated.email == added.email


async def test_should_return_none_when_update_user_not_exists(repository):
    assert await repository.update_user(uuid4(), {"is_active": False}) is None


# Refresh Tokens


async def test_should_store_and_return_active_refresh_token(repository):
    user = await repository.add_user(make_dict_user())
    hash_ = token_hash()

    stored = await repository.store_refresh_token(
        user_id=user.id,
        token_hash=hash_,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    active = await repository.get_active_refresh_token(hash_)

    assert active is not None
    assert active.id == stored.id
    assert active.user_id == user.id
    assert active.revoked_at is None


async def test_should_return_none_for_unknown_refresh_token(repository):
    assert await repository.get_active_refresh_token(token_hash()) is None


async def test_should_not_return_expired_refresh_token(repository):
    user = await repository.add_user(make_dict_user())
    hash_ = token_hash()
    await repository.store_refresh_token(
        user_id=user.id,
        token_hash=hash_,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    assert await repository.get_active_refresh_token(hash_) is None


async def test_should_revoke_refresh_token(repository):
    user = await repository.add_user(make_dict_user())
    hash_ = token_hash()
    await repository.store_refresh_token(
        user_id=user.id,
        token_hash=hash_,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    await repository.revoke_refresh_token(hash_)

    assert await repository.get_active_refresh_token(hash_) is None


async def test_should_not_fail_when_revoking_unknown_token(repository):
    await repository.revoke_refresh_token(token_hash())


async def test_should_revoke_all_tokens_for_user(repository):
    user = await repository.add_user(make_dict_user())
    other = await repository.add_user(make_dict_user())

    hashes = [token_hash(str(i)) for i in range(3)]
    for hash_ in hashes:
        await repository.store_refresh_token(
            user_id=user.id,
            token_hash=hash_,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

    other_hash = token_hash("other")
    await repository.store_refresh_token(
        user_id=other.id,
        token_hash=other_hash,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    await repository.revoke_all_for_user(user.id)

    for hash_ in hashes:
        assert await repository.get_active_refresh_token(hash_) is None
    
    # Tokens from other users cannot be affected
    assert await repository.get_active_refresh_token(other_hash) is not None
