from datetime import datetime

import pytz
from sqlalchemy import ForeignKey
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String

from app import db

timezone = pytz.timezone("America/Los_Angeles")


class BudgetCategories(db.Model):
    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, nullable=False, default=True)
    amount_in_cents = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))


class BudgetCategoriesRecords(db.Model):
    id = Column(Integer, primary_key=True)
    budget_categories_id = Column(
        Integer, ForeignKey("budget_categories.id"), nullable=False
    )
    is_active = Column(Boolean, nullable=False)
    amount_in_cents = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone))
    updated_at = Column(DateTime, default=datetime.now(timezone))
