"""Interactive (human) CLI for accounts.

`input()`-driven loops plus thin print wrappers over the display cores in
src.accounts.infra. The account operations are imported here so they remain
available in the interactive shell via `from src.accounts.commands import *`.
"""

from src.accounts.infra import (
    account_summary_text,
    adjust_account_value,
    create_new_account,
    deactivate_account,
    liquid_summary_text,
    update_account,
)
from src.accounts.model import Account, AccountType
from src.helpers import exit_keys
from src.transactions.model import TransactionType


def bulk_create_accounts(session) -> None:
    from rich.console import Console
    from src.accounts.view import make_account_creation_panel

    print(
        "Lets create some accounts! Enter 'quit' or 'exit' at any time to save and exit."
    )

    console = Console()

    while True:
        console.clear()
        console.print(make_account_creation_panel(session))

        name = input("Enter account name: ").strip()
        if name.lower() in exit_keys:
            return

        account_type_input = input("Enter account type number: ").strip()
        if account_type_input.lower() in exit_keys:
            return
        account_types = list(AccountType)
        try:
            account_type = account_types[int(account_type_input) - 1]
        except (ValueError, IndexError):
            print("Invalid account type selected!")
            continue

        value = input(
            "Enter account value in cents, click 'Enter' to set to 0: "
        ).strip()
        if value.lower() in exit_keys:
            return
        elif value == "":
            value = 0

        account_transaction_type_input = input(
            "Enter exclusive transaction type number, click 'Enter' to skip: "
        ).strip()
        account_transaction_type = None
        if account_transaction_type_input.lower() in exit_keys:
            return
        if account_transaction_type_input != "":
            account_transaction_type = TransactionType(
                int(account_transaction_type_input)
            )

        try:
            create_new_account(
                session,
                name,
                account_type,
                int(value),
                account_transaction_type,
            )
        except Exception as e:
            print(f"Error creating new account: {str(e)}")
            session.rollback()


def bulk_adjust_accounts(session) -> None:
    """Loops, letting the user pick an account by number and set its new value in cents. Useful for accounts (e.g. investments) whose value needs periodic manual correction."""
    from rich.console import Console
    from src.accounts.view import make_accounts_panel

    console = Console()

    while True:
        console.clear()
        console.print(make_accounts_panel(session))

        accounts: list[Account] = (
            session.query(Account)
            .filter(Account.is_active == True)
            .order_by(Account.created_at)
            .all()
        )
        account_mapping = {i: account for i, account in enumerate(accounts, 1)}
        print(
            "Lets adjust some account values! Enter 'quit' or 'exit' at any time to save and exit."
        )

        selection = input("Enter account number to adjust: ").strip()
        if selection.lower() in exit_keys:
            return
        account = (
            account_mapping.get(int(selection), None) if selection.isdigit() else None
        )
        if not account:
            print("Invalid account selected!")
            continue

        new_value = input("Enter new account value in cents: ").strip()
        if new_value.lower() in exit_keys:
            return

        reason = input("Enter reason (optional): ").strip()
        if reason.lower() in exit_keys:
            return
        if reason == "":
            reason = "Manual bulk adjustment"

        try:
            adjust_account_value(session, account.name, int(new_value), reason=reason)
        except Exception as e:
            print(f"Error adjusting account: {str(e)}")
            session.rollback()


def print_summary(session, include_budget=True) -> None:
    """Prints all active accounts and the total net value (with optional budget breakdown)."""
    print(account_summary_text(session, include_budget=include_budget))


def print_liquid_summary(session) -> None:
    """Prints all non-investing accounts and the total liquid net value."""
    print(liquid_summary_text(session))
