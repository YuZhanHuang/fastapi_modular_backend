import pytest
from fastapi.testclient import TestClient

from app.application.app import create_app
from tests.support.context import ScenarioContext


@pytest.fixture
def context() -> ScenarioContext:
    ctx = ScenarioContext()
    yield ctx
    ctx.run_cleanups()


@pytest.fixture
def container():
    """Use the same container instance bound by api/routers/carts.py for override to work."""
    from app.api.routers import carts

    yield carts.container


@pytest.fixture
def client(container) -> TestClient:
    app = create_app(container=container, init_db=False)
    with TestClient(app) as test_client:
        yield test_client
