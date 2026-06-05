import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Date, DateTime, Integer, String

from app import db


class TransactionType(enum.Enum):
    CREDIT = 1
    DEBIT = 2
    CASH = 3
    CHECK = 4
    VENMO = 5
    ADJUSTMENT = 6


class TransactionDirection(enum.Enum):
    INCREMENT = "increment"
    DECREMENT = "decrement"


class Transaction(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    direction = Column(Enum(TransactionDirection), nullable=False, default=TransactionDirection.DECREMENT)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    date_of_transaction = Column(Date, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now())
