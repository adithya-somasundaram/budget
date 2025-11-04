import enum
from datetime import datetime

import pytz
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Date, DateTime, Integer, String

from app import db

timezone = pytz.timezone("America/Los_Angeles")


class TransactionType(enum.Enum):
    CREDIT = 1
    DEBIT = 2
    CASH = 3
    CHECK = 4
    VENMO = 5


class Transaction(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    date_of_transaction = Column(Date, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))
