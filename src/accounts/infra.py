from src.accounts.model import Account, AccountType


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
