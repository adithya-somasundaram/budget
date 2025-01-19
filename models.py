import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app import db


class TransactionType(enum.Enum):
    CREDIT = 1
    DEBIT = 2
    CASH = 3
    CHECK = 4
    VENMO = 5


class CreditSource(enum.Enum):
    FIDELITY = 1
    KEYPOINT = 2


class Transaction(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class CreditPayment(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    credit_type = Column(Enum(CreditSource), nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
