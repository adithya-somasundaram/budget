from rich.panel import Panel

from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str
from src.view_helpers import new_table


def make_budget_category_panel(session):
    categories = (
        session.query(BudgetCategory)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )

    table = new_table("#", "Budget", "Amount")
    for i, cat in enumerate(categories, 1):
        table.add_row(str(i), cat.name, cents_to_dollars_str(cat.amount_in_cents))

    return Panel(table, title="Budget Categories"), {i: cat for i, cat in enumerate(categories, 1)}
