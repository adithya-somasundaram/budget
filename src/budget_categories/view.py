from rich.panel import Panel

from src.budget_categories.infra import get_budget_leftover
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

    leftover = get_budget_leftover(session)
    table.add_section()
    table.add_row("", "[bold]LEFTOVER[/bold]", f"[bold]{cents_to_dollars_str(leftover)}[/bold]")

    return Panel(table, title="Budget Categories"), {i: cat for i, cat in enumerate(categories, 1)}
