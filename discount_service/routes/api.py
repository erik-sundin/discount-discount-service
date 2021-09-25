import json
import logging
from typing import Awaitable, Callable
import falcon
import falcon.asgi
from falcon.media.validators import jsonschema
import falcon_jwt_guard
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, sessionmaker, selectinload
from sqlalchemy.future import select
from sqlalchemy.sql.expression import exists
from ..db import Discount, DiscountCode
from ..config import Config


class Authentication:
    def __init__(self, config: Config, auth: falcon_jwt_guard.Guard):
        self._auth = auth
        self.auth_required = False

    @jsonschema.validate(
        req_schema={
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "role": {"type": "string", "enum": ["brand", "user"]},
            },
            "minProperties": 2,
            "additionalProperties": False,
        }
    )
    async def on_get(self, req: falcon.asgi.Request, resp: falcon.asgi.Response):
        req_json = await req.get_media()
        token = self._auth.generate_token(req_json)
        resp.media = token


class Discounts:
    def __init__(self, config: Config, db_session: sessionmaker):
        self._config = config
        self._db_session = db_session
        self._logger = logging.getLogger(config.logger + " - " + __name__)
        self.auth_required = True

    @jsonschema.validate(
        resp_schema={
            "type": "object",
            "properties": {
                "availableDiscounts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "brand": {"type": "string"},
                            "percentage": {"type": "integer"},
                            "available": {"type": "integer"},
                        },
                    },
                }
            },
        }
    )
    async def on_get(self, req: falcon.asgi.Request, resp: falcon.asgi.Response):
        try:
            async with self._db_session() as session:
                async with session.begin():
                    result = await session.execute(select(Discount))
                    discounts = result.unique().scalars().all()
        except SQLAlchemyError as db_error:
            self._logger.error(db_error)
            raise falcon.HTTPInternalServerError(
                title="Database Access Error", description=db_error.__repr__()
            )
        resp.media = {
            "availableDiscounts": [
                {
                    "id": discount.id,
                    "name": discount.name,
                    "brand": discount.customer,
                    "percentage": discount.percentage,
                    "available": discount.available_codes,
                }
                for discount in discounts
                if discount.available_codes > 0
            ]
        }

    @jsonschema.validate(
        req_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                "nCodes": {"type": "integer", "minimum": 1},
            },
            "minProperties": 3,
            "additionalProperties": False,
        },
        resp_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "brand": {"type": "string"},
                "percentage": {"type": "integer"},
                "available": {"type": "integer"},
            },
            "minProperties": 5,
            "additionalProperties": False,
        },
    )
    async def on_post_create(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        if not req.context.claims["role"] == "brand":
            raise falcon.HTTPUnauthorized(
                title="Unauthorized", description="Only brands can create codes."
            )
        req_json: dict = await req.get_media()  # type: ignore
        try:
            new_discount = Discount(
                req.context.claims["username"],
                req_json["name"],
                req_json["percentage"],
                req_json["nCodes"],
            )
            async with self._db_session() as session:
                async with session.begin():
                    session.add(new_discount)
                await session.commit()
        except SQLAlchemyError as db_error:
            self._logger.error(db_error)
            raise falcon.HTTPInternalServerError(
                title="Database Access Error", description=db_error.__repr__()
            )
        resp.media = {
            "id": new_discount.id,
            "name": new_discount.name,
            "brand": new_discount.customer,
            "percentage": new_discount.percentage,
            "available": new_discount.available_codes,
        }
        resp.status = falcon.HTTP_CREATED

    @jsonschema.validate(
        resp_schema={
            "type": "object",
            "properties": {
                "registered": {"type": "boolean"},
                "code": {"type": "string"},
            },
            "minProperties": 2,
            "additionalProperties": False,
        },
    )
    async def on_post_claim(self, req, resp, id: str) -> None:
        try:
            id = int(id)
        except ValueError:
            raise falcon.HTTPBadRequest(title="No such discount")
        username = req.context.claims["username"]
        try:
            async with self._db_session() as session:
                async with session.begin():
                    discount: Discount = await session.get(
                        Discount, id, with_for_update=True
                    )
                    if not discount:
                        raise falcon.HTTPNotFound(title="No such discount")
                    if discount.available_codes < 1:
                        raise falcon.HTTPGone(title="Code exhausted")
                    user_claimed_discount = await session.execute(
                        select(
                            exists(DiscountCode)
                            .where(DiscountCode.discount_id == id)
                            .where(DiscountCode.user == username)
                        )
                    )
                    if user_claimed_discount.scalar():
                        raise falcon.HTTPConflict(
                            title="User has claimed this discount"
                        )
                    discount.claimed_codes += 1
                    new_code = DiscountCode(discount, username)
                    session.add(new_code)
                    try:
                        await session.commit()
                        user_code = str(new_code.id)
                    except SQLAlchemyError as write_error:
                        await session.rollback()
                        raise falcon.HTTPServiceUnavailable(title="Unable to register.")
        except SQLAlchemyError as db_error:
            self._logger.error(db_error)
            raise falcon.HTTPInternalServerError(
                title="Database Access Error", description=db_error.__repr__()
            )
        resp.media = {"registered": True, "code": user_code}
