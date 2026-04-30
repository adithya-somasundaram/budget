from datetime import datetime

from sqlalchemy import Boolean, Date, ForeignKey
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app import db


class TransferLedger(db.Model):
    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    amount_in_cents = Column(Integer, nullable=False)
    from_account_after_balance_in_cents = Column(Integer, nullable=False)
    to_account_after_balance_in_cents = Column(Integer, nullable=False)
    from_account_before_balance_in_cents = Column(Integer, nullable=False)
    to_account_before_balance_in_cents = Column(Integer, nullable=False)
    is_credit_payment = Column(Boolean, nullable=False)
    date_of_transaction = Column(Date, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now())
