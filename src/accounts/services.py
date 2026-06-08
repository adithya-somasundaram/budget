from sqlalchemy import case

from src.accounts.infra import create_new_account
from src.accounts.model import Account, AccountType
from src.helpers import cents_to_dollars_str, exit_keys
from src.transactions.model import TransactionDirection, TransactionType
from src.transactions.infra import create_transaction


def deactivate_account(
    session,
    name: str,
) -> int:
    account: Account = (
        session.query(Account)
        .filter(Account.name == name.upper(), Account.is_active == True)
        .first()
    )

    if not account:
        raise Exception(f"No active account found with name {name}!")

    account.is_active = False
    session.commit()

    print(f"Account {account.id} {name} deactived!")
    return account.id


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
    from src.budget_categories.services import print_budget_summary

    """Sums and returns all accounts. Also calculates total net value."""
    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True)
        .order_by(
            case((Account.type == AccountType.CREDIT, 1), else_=0), Account.created_at
        )
        .all()
    )
    output = ""
    grand_total = 0

    max_account_name_len = max(len(account.name) for account in accounts)

    for account in accounts:
        if account.type == AccountType.CREDIT:
            grand_total -= account.value_in_cents
        else:
            grand_total += account.value_in_cents
        output += f"{account.name:<{max_account_name_len}} : {'-' if account.type == AccountType.CREDIT else ''}{cents_to_dollars_str(account.value_in_cents)}\n"

    output += f"{'TOTAL':<{max_account_name_len}} : {cents_to_dollars_str(grand_total)}"
    print(output)

    if include_budget:
        print("\nBUDGET BREAKDOWN")
        print_budget_summary(session)


def print_liquid_summary(session) -> None:
    """Sums and returns all non-investing accounts. Also calculates total liquid net value."""
    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True, Account.type != AccountType.INVESTING)
        .order_by(
            case((Account.type == AccountType.CREDIT, 1), else_=0), Account.created_at
        )
        .all()
    )
    output = ""
    grand_total = 0

    max_account_name_len = max(len(account.name) for account in accounts)

    for account in accounts:
        if account.type == AccountType.CREDIT:
            grand_total -= account.value_in_cents
        else:
            grand_total += account.value_in_cents
        output += f"{account.name:<{max_account_name_len}} : {'-' if account.type == AccountType.CREDIT else ''}{cents_to_dollars_str(account.value_in_cents)}\n"

    output += f"{'TOTAL':<{max_account_name_len}} : {cents_to_dollars_str(grand_total)}"
    print(output)


def adjust_account_value(
    session, account_name: str, new_value_in_cents: int, reason: str = None
) -> None:
    account: Account = (
        session.query(Account)
        .filter(Account.name == account_name.upper(), Account.is_active == True)
        .first()
    )

    if not account:
        raise Exception(f"No active account found with name {account_name}!")

    adjustment_amount_in_cents = new_value_in_cents - account.value_in_cents
    direction = (
        TransactionDirection.INCREMENT
        if adjustment_amount_in_cents > 0
        else TransactionDirection.DECREMENT
    )

    create_transaction(
        session,
        abs(adjustment_amount_in_cents),
        TransactionType.ADJUSTMENT,
        f"Adjustment for account {account_name} for {adjustment_amount_in_cents} cents with reason: {reason}",
        account.id,
        direction=direction,
    )
