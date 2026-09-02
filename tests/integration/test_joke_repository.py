import uuid

import pytest
from tests.factories import make_joke

from fastapi_project.repository.jokes import JokeRepository


@pytest.fixture
def repository(session):
    return JokeRepository(session)


async def test_should_return_all_jokes(repository, session):
    for _ in range(5):
        await repository.add_joke(make_joke())
    await session.flush()

    jokes = await repository.get_all_jokes()
    assert len(jokes) == 5


async def test_should_return_jokes_by_tag(repository, session):
    for i in range(5):
        tag = "even" if i % 2 == 0 else "odd"
        await repository.add_joke(make_joke(tag=tag))
    await session.flush()
    jokes_by_tag = await repository.get_jokes_by_tag("odd")
    assert len(jokes_by_tag) == 3
    for j in jokes_by_tag:
        assert j.tag == "odd"


async def test_should_add_joke_and_return_joke_by_id(repository, session):
    joke = make_joke()

    await repository.add_joke(joke)
    await session.flush()
    session.expire_all()  # For SELECT go to database

    joke = repository.get_joke_by_id(joke.id)
    assert joke is not None


async def test_should_return_none_if_joke_not_exists_by_id(repository):
    random_id = uuid.uuid4()

    joke = repository.get_joke_by_id(random_id)
    assert joke is None


async def test_should_add_joke(repository, session):
    joke = make_joke()

    await repository.add_joke(joke)
    await session.flush()

    jokes = await repository.get_all_jokes()
    assert len(jokes) == 1


async def test_should_update_joke(repository, session):
    joke = make_joke()

    await repository.add_joke(joke)
    await session.flush()

    joke = repository.get_joke_by_id(joke.id)

    updated_joke = repository.update_joke(joke.id, {"tag": "updated"})
    await session.flush()

    assert updated_joke.id == joke.id

    assert updated_joke.tag == "updated"


async def test_should_delete_joke_returns_true(repository, session):
    joke = make_joke()

    await repository.add_joke(joke)
    await session.flush()

    joke = repository.get_joke_by_id(joke.id)

    result = repository.delete_joke(joke.id)
    await session.flush()

    jokes = await repository.get_all_jokes()
    assert len(jokes) == 0
    assert result


async def test_should_delete_joke_returns_false(repository, session):
    random_id = uuid.uuid4()
    result = repository.delete_joke(random_id)
    await session.flush()

    assert not result


# TODO Testar casos especiais nas funções
