from sqlalchemy import case

from src.accounts.model import Account, AccountType
from src.helpers import cents_to_dollars_str, exit_keys
from src.transactions.model import TransactionType
from src.transactions.infra import create_transaction


def create_new_account(
    session,
    name: str,
    account_type: AccountType,
    value_in_cents: int = None,
    transaction_type: TransactionType = None,
):
    # dupe check
    dupe: Account = (
        session.query(Account)
        .filter(Account.name == name.upper(), Account.type == account_type)
        .first()
    )

    if dupe and dupe.is_active:
        raise Exception(
            f"Duplicate account with type {account_type} and name {name}! Id: {dupe.id}"
        )
    elif dupe:
        dupe.is_active = True
        dupe.value_in_cents = value_in_cents or 0
        session.commit()
        return

    new_account = Account(
        name=name.upper(),
        type=account_type,
        value_in_cents=value_in_cents or 0,
        is_active=True,
        transaction_type=transaction_type,
    )

    session.add(new_account)
    session.commit()

    print(
        f"New Account created with name {name} and type {account_type}: {new_account.id}"
    )
    return new_account.id


def deactivate_account(
    session,
    name: str,
):
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


def bulk_create_accounts(session):
    print(
        "Lets create some accounts! Enter 'quit' or 'exit' at any time to save and exit."
    )

    name = None
    account_type = None
    value = 0

    while True:
        name = input("Enter account name: ").strip()
        if name.lower() in exit_keys:
            return

        account_type = input("Enter account type: ").strip().lower()
        if account_type.lower() in exit_keys:
            return

        value = input(
            "Enter account value in cents, click 'Enter' to set to 0: "
        ).strip()
        if value.lower() in exit_keys:
            return
        elif value == "":
            value = 0

        print(
            "Does the account have an exclusive transaction type (will be used in transactions):\n(1) Credit\n(2) Debit\n(3) Cash\n(4) Check\n(5) Venmo"
        )
        account_transaction_type_input = input().strip()
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
                AccountType(account_type),
                int(value),
                account_transaction_type,
            )
        except Exception as e:
            print(f"Error creating new account: {str(e)}")
            session.rollback()


def print_summary(session, include_budget=True):
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


def print_liquid_summary(session):
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
    session, account_name: str, adjustment_amount_in_cents: int, reason: str = None
):
    account: Account = (
        session.query(Account)
        .filter(Account.name == account_name.upper(), Account.is_active == True)
        .first()
    )

    if not account:
        raise Exception(f"No active account found with name {account_name}!")

    create_transaction(
        session,
        -adjustment_amount_in_cents,
        TransactionType.ADJUSTMENT,
        f"Adjustment for account {account_name} for {adjustment_amount_in_cents} cents with reason: {reason}",
        account_name,
    )
