from rich.columns import Columns
from rich.panel import Panel

from src.accounts.model import Account, AccountType
from src.view_helpers import (
    account_value_table,
    format_account_value,
    get_active_accounts,
    new_table,
    transaction_type_table,
)


def make_accounts_panel(session) -> Panel:
    """Builds a panel listing all active accounts, numbered for selection."""
    accounts = get_active_accounts(session)
    return Panel(account_value_table(accounts, title="Account"), title="Accounts")


def make_credit_payment_panel(session) -> Panel:
    """Builds a panel splitting accounts into credit (left) and paying/non-credit (right), each numbered independently."""
    credit_accounts = get_active_accounts(session, AccountType.CREDIT)
    paying_accounts = [
        a for a in get_active_accounts(session) if a.type != AccountType.CREDIT
    ]

    return Panel(
        Columns([
            account_value_table(credit_accounts, title="Credit Account"),
            account_value_table(paying_accounts, title="Paying Account"),
        ]),
        title="Credit Payment",
    )


def make_account_creation_panel(session) -> Panel:
    accounts: list[Account] = get_active_accounts(session)

    account_table = new_table("Account", "Type", "Balance", justify_first_right=False)
    for account in accounts:
        account_table.add_row(account.name, account.type.value, format_account_value(account))

    account_type_table = new_table("#", "Account Type")
    for i, t in enumerate(AccountType, 1):
        account_type_table.add_row(str(i), t.value)

    return Panel(
        Columns([account_table, account_type_table, transaction_type_table()]),
        title="Accounts",
    )
