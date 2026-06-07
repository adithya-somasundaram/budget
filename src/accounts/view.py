from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from src.accounts.model import Account, AccountType
from src.helpers import cents_to_dollars_str


def _account_table(accounts, title="Account") -> Table:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("#", justify="right")
    table.add_column(title)
    table.add_column("Balance", justify="right")
    for i, account in enumerate(accounts, 1):
        is_credit = account.type == AccountType.CREDIT
        value_str = ("-" if is_credit else "") + cents_to_dollars_str(account.value_in_cents)
        table.add_row(str(i), account.name, value_str)
    return table


def make_accounts_panel(session) -> Panel:
    """Builds a panel listing all active accounts, numbered for selection."""
    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True)
        .order_by(Account.created_at)
        .all()
    )
    return Panel(_account_table(accounts, title="Account"), title="Accounts")


def make_credit_payment_panel(session) -> Panel:
    """Builds a panel splitting accounts into credit (left) and paying/non-credit (right), each numbered independently."""
    credit_accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True, Account.type == AccountType.CREDIT)
        .order_by(Account.created_at)
        .all()
    )
    paying_accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True, Account.type != AccountType.CREDIT)
        .order_by(Account.created_at)
        .all()
    )

    return Panel(
        Columns([
            _account_table(credit_accounts, title="Credit Account"),
            _account_table(paying_accounts, title="Paying Account"),
        ]),
        title="Credit Payment",
    )


def make_account_creation_panel(session) -> Panel:
    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True)
        .order_by(Account.created_at)
        .all()
    )

    account_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    account_table.add_column("Account")
    account_table.add_column("Type")
    account_table.add_column("Balance", justify="right")
    for account in accounts:
        is_credit = account.type == AccountType.CREDIT
        value_str = ("-" if is_credit else "") + cents_to_dollars_str(account.value_in_cents)
        account_table.add_row(account.name, account.type.value, value_str)

    account_type_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    account_type_table.add_column("#", justify="right")
    account_type_table.add_column("Account Type")
    for i, t in enumerate(AccountType, 1):
        account_type_table.add_row(str(i), t.value)

    transaction_type_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    transaction_type_table.add_column("#", justify="right")
    transaction_type_table.add_column("Transaction Type")
    for i, name in [(1, "Credit"), (2, "Debit"), (3, "Cash"), (4, "Check"), (5, "Venmo")]:
        transaction_type_table.add_row(str(i), name)

    return Panel(
        Columns([account_table, account_type_table, transaction_type_table]),
        title="Accounts",
    )
