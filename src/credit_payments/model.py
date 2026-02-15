from datetime import datetime

from sqlalchemy import Date, ForeignKey
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app import db


class CreditPayment(db.Model):
    id = Column(Integer, primary_key=True)
    amount_in_cents = Column(Integer, nullable=False)
    credit_account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    date_of_transaction = Column(Date, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now())
