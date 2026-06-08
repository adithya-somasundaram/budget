from rich.table import Table

from src.accounts.model import Account, AccountType
from src.helpers import cents_to_dollars_str


def new_table(*columns, justify_first_right=True) -> Table:
    """Builds a Table with the consistent styling used across all panels."""
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    for i, column in enumerate(columns):
        justify = (
            "right"
            if (i == 0 and justify_first_right)
            or column in ("Balance", "Amount", "Remaining")
            else None
        )
        table.add_column(column, justify=justify)
    return table


def format_account_value(account) -> str:
    """Formats an account's value in cents as a dollar string, prefixed with '-' for credit accounts."""
    is_credit = account.type == AccountType.CREDIT
    return ("-" if is_credit else "") + cents_to_dollars_str(account.value_in_cents)


def get_active_accounts(session, account_type: AccountType = None) -> list:
    """Returns active accounts (name, value_in_cents, type), optionally filtered by type, ordered by creation."""
    query = session.query(Account.name, Account.value_in_cents, Account.type).filter(
        Account.is_active == True
    )
    if account_type is not None:
        query = query.filter(Account.type == account_type)
    return query.order_by(Account.created_at).all()


def account_value_table(accounts, title="Account", show_total=False) -> Table:
    """Builds a numbered table of accounts and their (credit-aware) balances, optionally with a TOTAL section."""
    table = new_table("#", title, "Balance")
    grand_total = 0
    for i, account in enumerate(accounts, 1):
        table.add_row(str(i), account.name, format_account_value(account))
        is_credit = account.type == AccountType.CREDIT
        grand_total += -account.value_in_cents if is_credit else account.value_in_cents
    if show_total:
        table.add_section()
        table.add_row(
            "",
            "[bold]TOTAL[/bold]",
            f"[bold]{cents_to_dollars_str(grand_total)}[/bold]",
        )
    return table


def transaction_type_table() -> Table:
    """Builds a numbered table listing the transaction types."""
    table = new_table("#", "Type")
    transaction_type_rows = [
        (1, "Credit"),
        (2, "Debit"),
        (3, "Cash"),
        (4, "Check"),
        (5, "Venmo"),
    ]
    for i, name in transaction_type_rows:
        table.add_row(str(i), name)
    return table
