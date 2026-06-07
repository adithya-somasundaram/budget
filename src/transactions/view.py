from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from src.accounts.infra import get_liquid_total
from src.accounts.model import Account, AccountType
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str


def make_summary_panel(session) -> Panel:
    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True)
        .order_by(Account.created_at)
        .all()
    )

    account_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    account_table.add_column("#", justify="right")
    account_table.add_column("Account")
    account_table.add_column("Balance", justify="right")

    grand_total = 0
    for i, account in enumerate(accounts, 1):
        is_credit = account.type == AccountType.CREDIT
        value_str = ("-" if is_credit else "") + cents_to_dollars_str(account.value_in_cents)
        account_table.add_row(str(i), account.name, value_str)
        grand_total += -account.value_in_cents if is_credit else account.value_in_cents
    account_table.add_section()
    account_table.add_row("", "[bold]TOTAL[/bold]", f"[bold]{cents_to_dollars_str(grand_total)}[/bold]")

    categories = (
        session.query(BudgetCategory.name, BudgetCategory.amount_in_cents)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name)
        .all()
    )

    budget_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    budget_table.add_column("#", justify="right")
    budget_table.add_column("Budget")
    budget_table.add_column("Remaining", justify="right")

    if categories:
        budget_total = 0
        for i, cat in enumerate(categories, 1):
            budget_table.add_row(str(i), cat.name, cents_to_dollars_str(cat.amount_in_cents))
            budget_total += cat.amount_in_cents
        liquid_total = get_liquid_total(session)
        leftover = liquid_total - budget_total
        budget_table.add_section()
        budget_table.add_row("", "[bold]LEFTOVER[/bold]", f"[bold]{cents_to_dollars_str(leftover)}[/bold]")

    type_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    type_table.add_column("#", justify="right")
    type_table.add_column("Type")
    for i, name in [(1, "Credit"), (2, "Debit"), (3, "Cash"), (4, "Check"), (5, "Venmo")]:
        type_table.add_row(str(i), name)
    type_table.add_section()
    type_table.add_row("[bold]Direction[/bold]", "")
    type_table.add_row("1", "Decrement")
    type_table.add_row("2", "Increment")

    return Panel(Columns([account_table, budget_table, type_table]), title="Summary")
