import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app import db


class CreditSource(enum.Enum):
    FIDELITY = 1
    KEYPOINT = 2


class CreditPayment(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    credit_type = Column(Enum(CreditSource), nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
