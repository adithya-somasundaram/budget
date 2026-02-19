from src.accounts.model import Account, AccountType
from src.helpers import cents_to_dollars_str
from src.transactions.model import TransactionType
from src.transactions.services import create_transaction


def create_new_account(
    session, name: str, account_type: AccountType, value_in_cents: int = None
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
    )

    session.add(new_account)
    session.commit()

    print(
        f"New Account created with name {name} and type {account_type}: {new_account.id}"
    )
    return new_account.id


# def update_account(
#     session,
#     name: str,
#     value_in_cents: int = None,
#     new_name: str = None,
#     new_account_type: AccountType = None,
# ):
#     account: Account = (
#         session.query(Account)
#         .filter(
#             Account.name == name.upper(),
#             Account.is_active == True,
#         )
#         .first()
#     )

#     if not account:
#         raise Exception(f"No active account found with name {name}!")

#     if value_in_cents:
#         account.value_in_cents = value_in_cents

#     if new_name:
#         account.name = new_name

#     if new_account_type:
#         account.type = new_account_type

#     session.commit()

#     print(
#         f"Account {account.id} upated with name {new_name or ''}, type {new_account_type or ''}, and value {value_in_cents or ''}"
#     )
#     return account.id


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


def bulk_create_accounts(session):
    print("Lets create some accounts! Enter 'quit' at any time to save and exit.")

    name = None
    account_type = None
    value = 0

    while True:
        name = input("Enter account name: ").strip()
        if name.lower() == "quit":
            return

        account_type = input("Enter account type: ").strip().lower()
        if account_type.lower() == "quit":
            return

        value = input("Enter account value, click 'Enter' to set to 0: ").strip()
        if value.lower() == "quit":
            return

        try:
            create_new_account(session, name, AccountType(account_type), int(value))
        except Exception as e:
            print(f"Error creating new account: {str(e)}")
            session.rollback()


def get_summary(session):
    """Sums and returns all accounts. Also calculates total net value."""
    accounts: list[Account] = (
        session.query(Account).filter(Account.is_active == True).all()
    )
    output = ""
    grand_total = 0
    for account in accounts:
        if account.type == AccountType.CREDIT:
            grand_total -= account.value_in_cents
        else:
            grand_total += account.value_in_cents
        output += "{0:10} : {1}\n".format(
            account.name, cents_to_dollars_str(account.value_in_cents)
        )

    return "{0:10}TOTAL: {1}".format(output, cents_to_dollars_str(grand_total))


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
