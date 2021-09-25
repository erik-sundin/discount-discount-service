import sqlalchemy
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy.sql.schema import ForeignKey
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
    max_codes = Column(Integer)
    claimed_codes = Column(Integer)
    codes = sqlalchemy.orm.relationship("DiscountCode", back_populates="discount")

    def __init__(self, customer: str, name: str, percentage: int, n_codes: int) -> None:
        if percentage not in range(0, 101):
            raise ValueError("Invalid percentage.")
        self.customer = customer
        self.name = name
        self.percentage = percentage
        self.max_codes = n_codes
        self.claimed_codes = 0

    @property
    def available_codes(self) -> int:
        return self.max_codes - self.claimed_codes


class DiscountCode(Base):
    """
    A code for a discount
    """

    __tablename__ = "codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_id = Column(Integer, ForeignKey("discounts.id"))
    discount = sqlalchemy.orm.relationship("Discount", back_populates="codes")
    user = Column(String)

    def __init__(self, discount: Discount, username: str) -> None:
        self.discount = discount
        self.user = username
