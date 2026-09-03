import uuid

import pytest
from tests.factories import make_dict_joke
from tests.fake import FakeJokeRepository

from fastapi_project.exceptions.exceptions import NotFoundError
from fastapi_project.schemas.jokes import JokeCreate, JokeUpdate
from fastapi_project.services.jokes import JokeService


async def test_should_get_jokes_with_pagination():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    paginated_jokes = await service.get_jokes()

    assert paginated_jokes.page == 1
    assert paginated_jokes.total == 1
    assert len(paginated_jokes.items) == 1


async def test_should_get_jokes_by_tag_with_pagination():
    test_tag = "test_tag"
    repository = FakeJokeRepository(
        initials=[
            make_dict_joke(tag=test_tag),
            make_dict_joke(),
            make_dict_joke(tag=test_tag),
        ]
    )
    service = JokeService(repository)

    paginated_jokes = await service.get_jokes_by_tag(test_tag)

    assert paginated_jokes.page == 1
    assert paginated_jokes.total == 2
    assert len(paginated_jokes.items) == 2


async def test_should_get_random_joke():
    tags = ["random_tag1", "random_tag2", "random_tag3"]
    repository = FakeJokeRepository(
        initials=[
            make_dict_joke(tag=tags[0]),
            make_dict_joke(tag=tags[1]),
            make_dict_joke(tag=tags[2]),
        ]
    )
    service = JokeService(repository)

    random_joke = await service.get_random_joke()

    assert random_joke is not None
    assert random_joke.tag in tags


async def test_should_raise_error_when_not_exists_joke_with_tag():
    repository = FakeJokeRepository(
        initials=[
            make_dict_joke(tag="tag1"),
            make_dict_joke(tag="tag2"),
            make_dict_joke(tag="tag3"),
        ]
    )
    service = JokeService(repository)

    with pytest.raises(NotFoundError) as exc:
        await service.get_random_joke(tag="random_tag")

    assert "No jokes with tag 'random_tag'" in str(exc.value)


async def test_should_raise_error_when_not_exists_available_jokes():
    repository = FakeJokeRepository()  # Without initial jokes
    service = JokeService(repository)

    with pytest.raises(NotFoundError) as exc:
        await service.get_random_joke()

    assert "No available jokes" in str(exc.value)


async def test_should_return_true_if_joke_exists_by_id():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    joke_id = (await repository.get_all_jokes())[0].id

    exists = await service.exists_joke_by_id(joke_id)

    assert exists


async def test_should_return_false_if_joke_not_exists_by_id():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    random_id = uuid.uuid4()
    exists = await service.exists_joke_by_id(random_id)

    assert not exists


async def test_should_return_joke_by_id():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    joke_id = (await repository.get_all_jokes())[0].id

    joke = await service.get_joke_by_id(joke_id)

    assert joke is not None
    assert joke.id == joke_id


async def test_should_raise_error_if_not_found_joke_by_id():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)
    random_id = uuid.uuid4()

    with pytest.raises(NotFoundError) as exc:
        await service.get_joke_by_id(random_id)

    assert "Joke not found with id: " in str(exc.value)


async def test_should_add_joke():
    repository = FakeJokeRepository()
    service = JokeService(repository)

    added_joke = await service.add_joke(JokeCreate(**make_dict_joke()))

    joke = (await repository.get_all_jokes())[0]

    assert joke is not None
    assert joke.id == added_joke.id
    assert joke.setup == added_joke.setup
    assert joke.punchline == added_joke.punchline
    assert joke.tag == added_joke.tag


async def test_should_update_joke():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    joke = (await repository.get_all_jokes())[0]

    updated_tag = "updated_tag"
    updated_joke = await service.update_joke(joke.id, JokeUpdate(tag=updated_tag))

    assert updated_joke is not None
    assert updated_joke.id == joke.id
    assert updated_joke.tag == updated_tag


async def test_should_raise_error_if_not_found_joke_by_id_when_update_joke():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    random_id = uuid.uuid4()

    with pytest.raises(NotFoundError) as exc:
        await service.update_joke(random_id, JokeUpdate(tag="updated_tag"))

    assert "Joke not found with id: " in str(exc.value)


async def test_should_delete_joke():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    joke_id = (await repository.get_all_jokes())[0].id

    await service.delete_joke(joke_id)

    jokes = await repository.get_all_jokes()

    assert len(jokes) == 0


async def test_should_raise_error_if_not_found_joke_by_id_when_delete_joke():
    repository = FakeJokeRepository(initials=[make_dict_joke()])
    service = JokeService(repository)

    random_id = uuid.uuid4()

    with pytest.raises(NotFoundError) as exc:
        await service.delete_joke(random_id)

    assert "Joke not found with id: " in str(exc.value)
