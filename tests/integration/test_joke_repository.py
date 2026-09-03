import uuid

import pytest
from tests.factories import make_dict_joke

from fastapi_project.repository.jokes import JokeRepository


@pytest.fixture
def repository(session):
    return JokeRepository(session)


async def test_should_return_all_jokes(repository, session):
    for _ in range(5):
        await repository.add_joke(make_dict_joke())
    await session.flush()

    jokes = await repository.get_all_jokes()
    assert len(jokes) == 5


async def test_should_return_jokes_by_tag(repository, session):
    tags = ["odd", "odd", "even"]
    for tag in tags:
        await repository.add_joke(make_dict_joke(tag=tag))

    jokes_by_tag = await repository.get_jokes_by_tag("odd")

    assert len(jokes_by_tag) == 2
    for j in jokes_by_tag:
        assert j.tag == "odd"


async def test_should_add_joke_and_return_joke_by_id(repository, session):
    added = await repository.add_joke(make_dict_joke())

    found = await repository.get_joke_by_id(added.id)

    assert found is not None
    assert found.id == added.id
    assert found.setup == added.setup


async def test_should_return_none_if_joke_not_exists_by_id(repository):
    random_id = uuid.uuid4()

    joke = await repository.get_joke_by_id(random_id)
    assert joke is None


async def test_should_add_joke(repository, session):
    await repository.add_joke(make_dict_joke())

    jokes = await repository.get_all_jokes()
    assert len(jokes) == 1


async def test_should_update_joke(repository, session):
    added = await repository.add_joke(make_dict_joke())

    updated_joke = await repository.update_joke(added.id, {"tag": "updated"})
    await session.flush()

    assert updated_joke.id == added.id
    assert updated_joke.tag == "updated"


async def test_should_delete_joke_returns_true(repository, session):
    added = await repository.add_joke(make_dict_joke())

    result = await repository.delete_joke(added.id)
    await session.flush()

    jokes = await repository.get_all_jokes()
    assert len(jokes) == 0
    assert result


async def test_should_delete_joke_returns_false(repository, session):
    random_id = uuid.uuid4()
    result = await repository.delete_joke(random_id)
    await session.flush()

    assert not result