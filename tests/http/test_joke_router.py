from uuid import uuid4

import pytest
from fastapi_pagination import Page, Params, set_params
from tests.factories import make_joke_model


async def test_get_jokes_should_returns_200(client, joke_service):
    jokes = [make_joke_model(), make_joke_model()]

    with set_params(Params(page=1, size=50)):
        joke_service.get_jokes.return_value = Page.create(
            items=jokes, total=len(jokes), params=Params(page=1, size=50)
        )

    response = await client.get("/jokes")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


async def test_get_random_joke_should_returns_200(client, joke_service):
    joke = make_joke_model()
    joke_service.get_random_joke.return_value = joke

    response = await client.get("/jokes/random")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(joke.id)
    assert body["setup"] == joke.setup
    assert body["tag"] == joke.tag


async def test_get_joke_by_id_should_returns_200(client, joke_service):
    joke = make_joke_model()
    joke_service.get_joke_by_id.return_value = joke

    response = await client.get(f"/jokes/{joke.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(joke.id)
    assert body["setup"] == joke.setup
    assert body["tag"] == joke.tag


# TODO: Passar body corretamente
async def test_add_joke_should_returns_201(client, joke_service):
    joke = make_joke_model()
    joke_service.add_joke.return_value = joke

    response = await client.post(
        "/jokes",
        json={"setup": joke.setup, "punchline": joke.punchline, "tag": joke.tag},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(joke.id)
    assert body["setup"] == joke.setup
    assert body["tag"] == joke.tag


# TODO: Retorna 307 == 422 no segundo assert
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"setup": "just this"},
        {"setup": "a", "punchline": "b", "tag": 123},
        {"setup": "", "punchline": "b", "tag": "x"},
    ],
    ids=["empty", "missing_fields", "tag_type_wrong", "empty_setup"],
)
async def test_add_joke_should_returns_422_with_invalid_payload(
    client, joke_service, payload
):
    response = await client.post("/jokes", json=payload)

    assert response.status_code == 422
    joke_service.add_joke.assert_not_awaited()


# TODO: Passar body corretamente
async def test_update_joke_should_returns_200(client, joke_service):
    joke = make_joke_model()
    joke_service.update_joke.return_value = joke

    response = await client.patch(f"/jokes/{joke.id}", json={"tag": "updated_tag"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(joke.id)
    assert body["setup"] == joke.setup
    assert body["tag"] == joke.tag


# TODO: Retorna 307 == 422 no segundo assert
@pytest.mark.parametrize(
    "payload",
    [
        {"setup": "a", "punchline": "b", "tag": 123},
    ],
    ids=["tag_type_wrong"],
)
async def test_update_joke_should_returns_422_with_invalid_payload(
    client, joke_service, payload
):
    response = await client.patch(f"/jokes/{str(uuid4())}", json=payload)

    assert response.status_code == 422
    joke_service.add_joke.assert_not_awaited()


# TODO: Passar body corretamente
async def test_delete_joke_should_returns_204(client, joke_service):
    joke_service.delete_joke.return_value = None

    response = await client.delete(f"/jokes/{str(uuid4())}")

    assert response.status_code == 204
