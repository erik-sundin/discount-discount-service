import json
import logging
import falcon
import falcon.asgi
from falcon.media.validators import jsonschema
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, sessionmaker, selectinload
from sqlalchemy.future import select
from ..db import Discount
from ..config import Config


class Discounts:

    def __init__(self, config: Config, db_session: sessionmaker):
        self._config = config
        self._db_session = db_session
        self._logger = logging.getLogger(config.logger + " - " + __name__)

    async def on_get(self, req: falcon.asgi.Request, resp: falcon.asgi.Response):
        try:
            async with self._db_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Discount).options(joinedload(Discount.codes))
                    )
                    discounts = result.unique().scalars()
        except SQLAlchemyError as db_error:
            self._logger.error(db_error)
            raise falcon.HTTPInternalServerError(
                title="Database Access Error", description=db_error.__repr__())
        resp.media = {
            'availableDiscounts':  [
                {
                    "id": discount.id,
                    "name": discount.name,
                    "brand": discount.customer,
                    "percentage": discount.percentage,
                    "available": len([code for code in discount.codes if not code.claimed])
                } for discount in discounts if len(discount.unclaimed_codes) > 0]}

    @jsonschema.validate(req_schema={
        "type": "object",
        "properties": {
                "name": {"type": "string"},
                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                "nCodes": {"type": "integer", "minimum": 1}
        },
        "minProperties": 3,
        "additionalProperties": False
    })
    async def on_post_create(self, req: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        req_json: dict = await req.get_media()  # type: ignore
        try:
            new_discount = Discount(
                "testdata", req_json['name'], req_json["percentage"], req_json["nCodes"])
            async with self._db_session() as session:
                async with session.begin():
                    session.add(new_discount)
                await session.commit()
        except SQLAlchemyError as db_error:
            self._logger.error(db_error)
            raise falcon.HTTPInternalServerError(
                title="Database Access Error", description=db_error.__repr__())

    @jsonschema.validate(req_schema={
        "type": "object",
        "properties": {
            "username": {"type": "string"},
        },
        "minProperties": 1,
        "additionalProperties": False
    })
    async def on_post_claim(self, req: falcon.asgi.Request, resp: falcon.asgi.Response, id: str) -> None:
        try:
            id = int(id)
        except ValueError:
            raise falcon.HTTPNotFound(title="No such discount")
        req_json = await req.get_media()
        try:
            async with self._db_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Discount).where(Discount.id == id).options(
                            selectinload(Discount.codes))
                    )
                    discount = result.scalar()
                    if not discount or len(discount.unclaimed_codes) < 1:
                        resp.media = {"registered": False, "code": None, "reason": "No codes available"}
                        return
                    user_code = discount.unclaimed_codes[0]
                    user_code.claimed = True
                    user_code.user = req_json['username']
                    user_discount_code = user_code.id
                    try:
                        await session.commit()
                    except SQLAlchemyError as write_error:
                        await session.rollback()
                        resp.media = {"registered": False, "code": None, "reason": "No codes available"}
                        return
        except SQLAlchemyError as db_error:
            self._logger.error(db_error)
            raise falcon.HTTPInternalServerError(
                title="Database Access Error", description=db_error.__repr__())
        # Notify brand of claimed discount here in some sane way.
        resp.media = {"registered": True, "code": str(user_discount_code)}
