from rich.panel import Panel
from rich.table import Table

from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str


def make_budget_category_panel(session):
    categories = (
        session.query(BudgetCategory)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("#", justify="right")
    table.add_column("Budget")
    table.add_column("Amount", justify="right")
    for i, cat in enumerate(categories, 1):
        table.add_row(str(i), cat.name, cents_to_dollars_str(cat.amount_in_cents))

    return Panel(table, title="Budget Categories"), {i: cat for i, cat in enumerate(categories, 1)}
