
import sqlalchemy
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()

class Discount(Base):
    """
    A discount registered with a brand.
    """
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True)
    customer = Column(String)
    name = Column(String)
    percentage = Column(Integer)
    codes = sqlalchemy.orm.relationship("DiscountCode", back_populates='discount')

    def __init__(self, customer: str, name: str, percentage: int, n_codes: int) -> None:
        if percentage not in range(0,101):
            raise ValueError("Invalid percentage.")
        self.customer = customer
        self.name = name
        self.percentage = percentage
        self.codes = [DiscountCode(self) for i in range(n_codes)]

    @property
    def unclaimed_codes(self) -> list:
        return [code for code in self.codes if not code.claimed]
        


class DiscountCode(Base):
    """
    A code for a discount
    """
    __tablename__ = "codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_id = Column(Integer, ForeignKey('discounts.id'))
    discount = sqlalchemy.orm.relationship("Discount", back_populates="codes")
    user = Column(String)
    claimed = Column(Boolean)


    def __init__(self, discount: Discount) -> None:
        self.discount = discount


