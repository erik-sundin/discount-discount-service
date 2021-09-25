"""
Author: esundin
"""
from typing import Optional
from falcon import middleware
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import falcon
import falcon.asgi
from falcon_jwt_guard import Guard
from .config import Config
from .db import Base, Discount
from .routes.api import Authentication, Discounts


class JwtWare:
    def __init__(self, config: Config):
        self._auth = Guard(config.jwt_key)

    async def process_resource(self, req, resp, resource, params):
        if resource.auth_required:
            self._auth(req, resp, resource, params)


def create_db(config: Optional[Config] = None) -> sessionmaker:
    """
    Sqlalchemy.orm.sessionmaker context manager for given config.
    """
    config = config or Config()
    async_db_engine = create_async_engine(config.db_url, pool_size=50)
    db_engine = sqlalchemy.create_engine(config.db_url.replace("+asyncpg", ""))
    Base.metadata.create_all(db_engine)
    return sessionmaker(async_db_engine, expire_on_commit=False, class_=AsyncSession)


def create_app(config: Optional[Config] = None) -> falcon.asgi.App:
    """
    falcon.asgi.App with initialized routes.
    """
    config = config or Config()
    auth = Guard(config.jwt_key)
    db_session = create_db(config)
    falcon_app = falcon.asgi.App(middleware=[JwtWare(config)])
    falcon_app.add_route("/discounts", Discounts(config, db_session))
    falcon_app.add_route(
        "/discount/create", Discounts(config, db_session), suffix="create"
    )
    falcon_app.add_route(
        "/discount/{id}/claim", Discounts(config, db_session), suffix="claim"
    )
    falcon_app.add_route("/auth", Authentication(config, auth))
    return falcon_app
