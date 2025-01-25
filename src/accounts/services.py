from src.accounts.model import Account
from src.transactions.model import TransactionType


def create_new_account(
    session, name: str, account_type: TransactionType, value_in_usd_cents: int = None
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
        dupe.value_in_cents = value_in_usd_cents or 0
        session.commit()
        return

    new_account = Account(
        name=name.upper(),
        type=account_type,
        value_in_usd_cents=value_in_usd_cents or 0,
        is_active=True,
    )

    session.add(new_account)
    session.commit()

    print(
        f"New Account created with name {name} and type {account_type}: {new_account.id}"
    )
    return new_account.id


def update_account(
    session,
    name: str,
    value_in_usd_cents: int = None,
    new_name: str = None,
    new_account_type: TransactionType = None,
):
    account: Account = (
        session.query(Account)
        .filter(
            Account.name == name.upper(),
            Account.is_active == True,
        )
        .first()
    )

    if not account:
        raise Exception(f"No active account found with name {name}!")

    if value_in_usd_cents:
        account.value_in_cents = value_in_usd_cents

    if new_name:
        account.name = new_name

    if new_account_type:
        account.type = new_account_type

    session.commit()

    print(
        f"Account {account.id} upated with name {new_name or ''}, type {new_account_type or ''}, and value {value_in_usd_cents or ''}"
    )
    return account.id


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


def transfer(session, amount_in_cents, to_account: str, from_account: str):
    to_account_obj: Account = (
        session.query(Account)
        .filter(Account.name == from_account.upper(), Account.is_active == True)
        .first()
    )
    if not to_account_obj:
        raise Exception(f"No active account found with name {to_account}!")

    from_account_obj: Account = (
        session.query(Account)
        .filter(Account.name == from_account.upper(), Account.is_active == True)
        .first()
    )

    if not from_account_obj:
        raise Exception(f"No active account found with name {from_account}!")

    if amount_in_cents > from_account_obj.value_in_cents:
        raise Exception(
            f"{amount_in_cents} greater than accounts value {from_account_obj.value_in_cents}!"
        )

    to_account_obj.value_in_cents += amount_in_cents
    from_account_obj.value_in_cents -= amount_in_cents

    session.commit()
