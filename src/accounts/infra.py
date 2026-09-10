from sqlalchemy import case

from src.accounts.model import Account, AccountType
from src.helpers import cents_to_dollars_str
from src.transactions.infra import create_transaction
from src.transactions.model import TransactionDirection, TransactionType


def get_all_accounts_mapping(
    session, account_type: AccountType = None
) -> dict[int, Account]:
    """Returns dict mapping an integer to and account. Good for user input."""
    query = session.query(Account.id, Account.name, Account.type, Account.transaction_type).filter(
        Account.is_active == True
    )
    if account_type:
        query = query.filter(Account.type == account_type)
    accounts: list[Account] = query.order_by(Account.created_at).all()

    return {i: account for i, account in enumerate(accounts, 1)}


def get_active_account_by_name(session, name: str) -> Account:
    """Returns the active account with this name (case-insensitive), or None.

    Shared lookup used by the human CLI and the agent tools to resolve a name the
    user typed into an account row.
    """
    return (
        session.query(Account)
        .filter(Account.name == name.upper(), Account.is_active == True)
        .first()
    )


def get_liquid_total(session) -> int:
    """Returns total liquid assets in cents, excluding investing accounts. Credit accounts are subtracted."""
    accounts: list[Account] = (
        session.query(Account.value_in_cents, Account.type)
        .filter(Account.is_active == True, Account.type != AccountType.INVESTING)
        .all()
    )
    total = 0
    for account in accounts:
        if account.type == AccountType.CREDIT:
            total -= account.value_in_cents
        else:
            total += account.value_in_cents
    return total


def create_new_account(
    session,
    name: str,
    account_type: AccountType,
    value_in_cents: int = None,
    transaction_type: TransactionType = None,
) -> int:
    """Creates a new account with given name and type. Returns new account id."""
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


def deactivate_account(session, name: str) -> int:
    """Soft-deletes the active account with this name. Returns its id."""
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


def adjust_account_value(
    session, account_name: str, new_value_in_cents: int, reason: str = None
) -> None:
    """Sets an account to a new absolute value, recording the delta as an ADJUSTMENT transaction."""
    account: Account = (
        session.query(Account)
        .filter(Account.name == account_name.upper(), Account.is_active == True)
        .first()
    )

    if not account:
        raise Exception(f"No active account found with name {account_name}!")

    adjustment_amount_in_cents = new_value_in_cents - account.value_in_cents
    increasing_value = adjustment_amount_in_cents > 0
    # create_transaction inverts direction for credit accounts (a decrement on a
    # credit account raises what is owed), so pick the direction that makes the
    # stored value actually land on new_value_in_cents regardless of account type.
    is_credit = account.type == AccountType.CREDIT
    if is_credit:
        direction = (
            TransactionDirection.DECREMENT
            if increasing_value
            else TransactionDirection.INCREMENT
        )
    else:
        direction = (
            TransactionDirection.INCREMENT
            if increasing_value
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


def update_account(
    session,
    account_name: str,
    new_name: str = None,
    new_type: AccountType = None,
    new_transaction_type: TransactionType = None,
) -> None:
    """Updates an account's name, type, and/or exclusive transaction type.

    Only the fields you pass are changed. Does not touch the account's value
    (use adjust_account_value for that). Changing type affects how the account is
    counted in totals (credit balances are subtracted).
    """
    account: Account = (
        session.query(Account)
        .filter(Account.name == account_name.upper(), Account.is_active == True)
        .first()
    )

    if not account:
        raise Exception(f"No active account found with name {account_name}!")

    if new_name:
        target = new_name.upper()
        existing = (
            session.query(Account)
            .filter(Account.name == target, Account.id != account.id)
            .first()
        )
        if existing:
            raise Exception(f"An account named {target} already exists!")
        account.name = target

    if new_type:
        account.type = new_type

    if new_transaction_type:
        account.transaction_type = new_transaction_type

    session.commit()
    print(f"Updated account {account.name}")


def account_summary_text(session, include_budget=True) -> str:
    """Builds the account summary string (all active accounts + net total).

    Returns the text so both the human CLI (which prints it) and the agent (which
    embeds it in a reply) can share the same compute+format logic. When
    include_budget is set, the budget breakdown is appended.
    """
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

    if include_budget:
        from src.budget_categories.infra import budget_summary_text

        output += "\n\nBUDGET BREAKDOWN\n"
        output += budget_summary_text(session)

    return output


def liquid_summary_text(session) -> str:
    """Builds the liquid summary string (all non-investing accounts + liquid total)."""
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
    return output
