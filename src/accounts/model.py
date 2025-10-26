import enum
from datetime import datetime

import pytz
from sqlalchemy import Enum, Index, event, text
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String

from app import db

timezone = pytz.timezone("America/Los_Angeles")


class AccountType(enum.Enum):
    CREDIT = 1
    DEBIT = 2
    CASH = 3
    CHECK = 4
    VENMO = 5
    INVESTING = 6


class Account(db.Model):
    id = Column(Integer, primary_key=True)
    value_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))

    __table_args__ = (
        # Unique only when is_active = 1 (i.e., true)
        Index(
            "uq_active_name",
            "name",
            unique=True,
            sqlite_where=text("is_active = 1"),
        ),
    )


class AccountRecords(db.Model):
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    value_in_cents = Column(Integer, nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))


@event.listens_for(Account, "after_insert")
@event.listens_for(Account, "after_update")
def create_account_record_on_update(_, connection, target):
    connection.execute(
        AccountRecords.__table__.insert(),
        {
            "account_id": target.id,
            "value_in_cents": target.value_in_cents,
            "type": target.type,
            "name": target.name,
            "is_active": target.is_active,
        },
    )
