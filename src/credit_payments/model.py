import enum
from datetime import datetime

import pytz
from sqlalchemy import Enum
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app import db

timezone = pytz.timezone("America/Los_Angeles")


class CreditSource(enum.Enum):
    FIDELITY = 1
    KEYPOINT = 2


class CreditPayment(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    credit_type = Column(Enum(CreditSource), nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))
