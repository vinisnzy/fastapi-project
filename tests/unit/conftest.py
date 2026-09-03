import pytest
from fastapi_pagination import Params, set_params


@pytest.fixture(autouse=True)
def _pagination_params():
    with set_params(Params(page=1, size=50)):
        yield
