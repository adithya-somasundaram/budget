from datetime import datetime

import pytz
from sqlalchemy import ForeignKey, Index, event, text
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String

from app import db

timezone = pytz.timezone("America/Los_Angeles")


class BudgetCategory(db.Model):
    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, nullable=False, default=True)
    amount_in_cents = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
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


class BudgetCategoryRecords(db.Model):
    id = Column(Integer, primary_key=True)
    budget_category_id = Column(
        Integer, ForeignKey("budget_categories.id"), nullable=False
    )
    is_active = Column(Boolean, nullable=False)
    amount_in_cents = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))


@event.listens_for(BudgetCategory, "after_insert")
@event.listens_for(BudgetCategory, "after_update")
def create_account_record_on_update(_, connection, target):
    connection.execute(
        BudgetCategoryRecords.__table__.insert(),
        {
            "budget_category_id": target.id,
            "is_active": target.is_active,
            "amount_in_cents": target.amount_in_cents,
            "name": target.name,
        },
    )
