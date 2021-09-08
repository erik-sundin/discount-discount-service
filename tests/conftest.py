import asyncio
from typing import Callable
import pytest
import falcon.testing
import falcon.asgi
from discount_service.app import create_app, Config


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """
    Creates an instance of the default event loop for the test session.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def database_url() -> str:
    return 'postgresql+asyncpg://postgres:verysecret@postgres:5432/discount_service_test'


@pytest.fixture(scope="session")
def init_database() -> Callable:
    from discount_service.app import Base

    return Base.metadata.create_all


@pytest.fixture()
def client(dbsession, database_url: str) -> Callable:
    def _client() -> falcon.testing.TestClient:
        config = Config()
        config.db_url = database_url
        app = create_app(config=config)
        return falcon.testing.TestClient(app)

    return _client
