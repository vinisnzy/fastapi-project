from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from tests.factories import make_dict_user
from tests.fake import FakeUserRepository

from fastapi_project.core.secret import decode_token, hash_password, hash_token
from fastapi_project.exceptions.exceptions import ConflictError, UnauthorizedError
from fastapi_project.models import User
from fastapi_project.schemas.auth import TokenPair, UserCreate
from fastapi_project.services.auth import AuthService

PASSWORD = "secret_password_123"
HASHED_PASSWORD = hash_password(PASSWORD)


@pytest.fixture
def service(settings):
    def _factory(initials=None) -> AuthService:
        repository = FakeUserRepository(initials=initials)
        return AuthService(repository, settings)

    return _factory


async def test_should_register_user(service):
    auth: AuthService = service()

    user: User = await auth.register(
        UserCreate(email="new@email.com", password=PASSWORD)
    )

    assert user.email == "new@email.com"
    assert user.hashed_password != PASSWORD
    assert await auth.repository.get_user_by_email("new@email.com") is not None


async def test_should_raises_error_when_email_already_registered(service):
    auth: AuthService = service(initials=[make_dict_user(email="taken@email.com")])

    with pytest.raises(ConflictError) as exc:
        await auth.register(UserCreate(email="taken@email.com", password=PASSWORD))

    assert "Email already registered" in str(exc.value)


async def test_should_authenticate(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    user: User = await auth.authenticate(email="user@email.com", password=PASSWORD)

    assert user.email == "user@email.com"
    assert user.hashed_password == HASHED_PASSWORD


async def test_should_raises_error_when_user_not_exists_by_email(service):
    auth: AuthService = service()

    with pytest.raises(UnauthorizedError) as exc:
        await auth.authenticate(email="user@email.com", password=PASSWORD)

    assert "Invalid credentials" in str(exc.value)


async def test_should_raises_error_when_password_is_wrong(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    with pytest.raises(UnauthorizedError) as exc:
        await auth.authenticate(email="user@email.com", password="wrong_password")

    assert "Invalid credentials" in str(exc.value)


async def test_should_raises_error_when_user_is_unactive(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(
                email="user@email.com", hashed_password=HASHED_PASSWORD, is_active=False
            )
        ]
    )

    with pytest.raises(UnauthorizedError) as exc:
        await auth.authenticate(email="user@email.com", password=PASSWORD)

    assert "Invalid credentials" in str(exc.value)


async def test_should_issue_access_and_refresh_tokens(service, settings):
    auth: AuthService = service(initials=[make_dict_user()])
    user = await auth.repository.get_user_by_email(
        next(iter(auth.repository.users.values()))["email"]
    )

    token_pair: TokenPair = await auth.issue_tokens(user)

    access_decoded = decode_token(token_pair.access_token, "access", settings)
    refresh_decoded = decode_token(token_pair.refresh_token, "refresh", settings)

    assert token_pair.token_type == "bearer"

    assert access_decoded["sub"] == str(user.id)
    assert access_decoded["type"] == "access"

    assert refresh_decoded["sub"] == str(user.id)
    assert refresh_decoded["type"] == "refresh"

    assert hash_token(token_pair.refresh_token) in auth.repository.tokens


async def test_should_login_return_access_and_refresh_token(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    token_pair: TokenPair = await auth.login(email="user@email.com", password=PASSWORD)

    assert token_pair.access_token is not None
    assert token_pair.refresh_token is not None


async def test_should_login_raises_error_when_credentials_is_invalid(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    with pytest.raises(UnauthorizedError) as exc:
        await auth.login(email="user@email.com", password="wrong_password")

    assert "Invalid credentials" in str(exc.value)


async def test_should_rotate_refresh_token(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    tokens: TokenPair = await auth.login(email="user@email.com", password=PASSWORD)

    new_tokens: TokenPair = await auth.refresh(tokens.refresh_token)

    assert tokens.refresh_token != new_tokens.refresh_token

    old = auth.repository.tokens[hash_token(tokens.refresh_token)]
    assert old["revoked_at"] is not None

    assert (
        await auth.repository.get_active_refresh_token(
            hash_token(new_tokens.refresh_token)
        )
        is not None
    )


async def test_should_raises_error_when_token_is_malformed(service):
    auth: AuthService = service()
    with pytest.raises(UnauthorizedError) as exc:
        await auth.refresh("malformed-token")
    assert "Invalid refresh token" in str(exc.value)


async def test_should_raises_error_when_using_access_token(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    tokens: TokenPair = await auth.login(email="user@email.com", password=PASSWORD)

    with pytest.raises(UnauthorizedError) as exc:
        await auth.refresh(tokens.access_token)

    assert "Invalid refresh token" in str(exc.value)


async def test_should_raises_error_when_refresh_token_is_expired(service, settings):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )
    user_id = next(iter(auth.repository.users))
    expired_token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": datetime.now(UTC) - timedelta(days=30),
            "exp": datetime.now(UTC) - timedelta(days=1),
        },
        key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(UnauthorizedError) as exc:
        await auth.refresh(expired_token)

    assert "Invalid refresh token" in str(exc.value)


async def test_should_revoke_all_tokens_on_refresh_token_reuse(service):
    """Reused token detection"""
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    first_use = await auth.login(email="user@email.com", password=PASSWORD)
    second_use = await auth.refresh(first_use.refresh_token)

    with pytest.raises(UnauthorizedError) as exc:
        await auth.refresh(first_use.refresh_token)

    assert "Refresh token revoked" in str(exc.value)
    # All user tokens must be downed
    assert (
        await auth.repository.get_active_refresh_token(
            hash_token(second_use.refresh_token)
        )
        is None
    )


async def test_should_raises_error_when_user_became_inactive_before_refresh(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    tokens = await auth.login(email="user@email.com", password=PASSWORD)

    user_id = next(iter(auth.repository.users))
    await auth.repository.update_user(user_id, {"is_active": False})

    with pytest.raises(UnauthorizedError) as exc:
        await auth.refresh(tokens.refresh_token)

    assert "Invalid credentials" in str(exc.value)


async def test_should_revoke_refresh_token_on_logout(service):
    auth: AuthService = service(
        initials=[
            make_dict_user(email="user@email.com", hashed_password=HASHED_PASSWORD)
        ]
    )

    tokens = await auth.login(email="user@email.com", password=PASSWORD)

    await auth.logout(tokens.refresh_token)

    assert (
        await auth.repository.get_active_refresh_token(hash_token(tokens.refresh_token))
        is None
    )
