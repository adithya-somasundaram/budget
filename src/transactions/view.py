from rich.columns import Columns
from rich.panel import Panel

from src.accounts.infra import get_liquid_total
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str
from src.view_helpers import account_value_table, get_active_accounts, new_table, transaction_type_table


def make_summary_panel(session) -> Panel:
    accounts = get_active_accounts(session)
    account_table = account_value_table(accounts, title="Account", show_total=True)

    categories = (
        session.query(BudgetCategory.name, BudgetCategory.amount_in_cents)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name)
        .all()
    )

    budget_table = new_table("#", "Budget", "Remaining")

    if categories:
        budget_total = 0
        for i, cat in enumerate(categories, 1):
            budget_table.add_row(str(i), cat.name, cents_to_dollars_str(cat.amount_in_cents))
            budget_total += cat.amount_in_cents
        liquid_total = get_liquid_total(session)
        leftover = liquid_total - budget_total
        budget_table.add_section()
        budget_table.add_row("", "[bold]LEFTOVER[/bold]", f"[bold]{cents_to_dollars_str(leftover)}[/bold]")

    type_table = transaction_type_table()
    type_table.add_section()
    type_table.add_row("[bold]Direction[/bold]", "")
    type_table.add_row("1", "Decrement")
    type_table.add_row("2", "Increment")

    return Panel(Columns([account_table, budget_table, type_table]), title="Summary")
