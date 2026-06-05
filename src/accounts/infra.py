from src.accounts.model import Account, AccountType
from src.transactions.model import TransactionType


def get_all_accounts_mapping(
    session, account_type: AccountType = None
) -> dict[int, Account]:
    """Returns dict mapping an integer to and account. Good for user input."""
    query = session.query(Account.id, Account.name, Account.transaction_type).filter(
        Account.is_active == True
    )
    if account_type:
        query = query.filter(Account.type == account_type)
    accounts: list[Account] = query.order_by(Account.created_at).all()

    return {i: account for i, account in enumerate(accounts, 1)}


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
