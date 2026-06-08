from rich.panel import Panel

from src.accounts.infra import get_liquid_total
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
    budget_total = 0
    for i, cat in enumerate(categories, 1):
        table.add_row(str(i), cat.name, cents_to_dollars_str(cat.amount_in_cents))
        budget_total += cat.amount_in_cents

    leftover = get_liquid_total(session) - budget_total
    table.add_section()
    table.add_row("", "[bold]LEFTOVER[/bold]", f"[bold]{cents_to_dollars_str(leftover)}[/bold]")

    return Panel(table, title="Budget Categories"), {i: cat for i, cat in enumerate(categories, 1)}
