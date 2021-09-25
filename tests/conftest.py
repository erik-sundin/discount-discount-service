import asyncio
from discount_service.db import Base
from typing import Callable
import pytest
import falcon.testing
import falcon.asgi
import sqlalchemy.ext.asyncio
from discount_service.app import create_app, Config


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """
    Creates an instance of the default event loop for the test session.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def database_url() -> str:
    return (
        "postgresql+asyncpg://postgres:verysecret@postgres:5432/discount_service_test"
    )


@pytest.fixture(scope="session")
def init_database() -> Callable:
    from discount_service.app import Base

    return Base.metadata.create_all


@pytest.fixture()
def auth_brand(client: falcon.testing.TestClient):
    resp = client.simulate_get(
        "/auth",
        content_type="application/json",
        json={"username": "test_brand", "role": "brand"},
    )
    return resp.text.strip('"')


@pytest.fixture()
def auth_user(client: falcon.testing.TestClient):
    resp = client.simulate_get(
        "/auth",
        content_type="application/json",
        json={"username": "test_brand", "role": "user"},
    )
    return resp.text.strip('"')


@pytest.fixture()
async def client(
    dbsession: sqlalchemy.ext.asyncio.AsyncSession, database_url: str
) -> falcon.testing.TestClient:
    config = Config()
    config.db_url = database_url
    config.jwt_key = "nonsecret"
    app = create_app(config=config)
    yield falcon.testing.TestClient(app)
    async with dbsession as session:
        await session.execute("DROP TABLE codes;")
        await session.execute("DROP TABLE discounts;")
