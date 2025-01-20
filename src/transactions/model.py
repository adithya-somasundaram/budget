import enum
from datetime import datetime

import pytz
from sqlalchemy import Enum
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app import db
from src.credit_payments.model import CreditSource

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
    credit_type = Column(Enum(CreditSource), nullable=True)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))
