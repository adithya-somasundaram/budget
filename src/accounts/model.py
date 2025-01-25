from datetime import datetime

import pytz
from sqlalchemy import Enum
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String

from app import db
from src.transactions.model import TransactionType

timezone = pytz.timezone("America/Los_Angeles")


class Account(db.Model):
    id = Column(Integer, primary_key=True)
    value_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))


class AccountRecords(db.Model):
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    value_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))
