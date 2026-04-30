from datetime import datetime

from accounts.services import get_all_accounts_mapping
from src.accounts.model import Account
from src.credit_payments.model import CreditPayment
from src.helpers import pacific_timezone
from src.transactions.model import TransactionType
from src.transactions.services import create_transaction


def transfer_input(session):
    """Transfers amount from one account to another. Both accounts must be active."""
    exit_keys = set(["quit", ""])
    amount_in_cents = input("Enter transfer amount in cents: ").strip()
    if amount_in_cents.lower() in exit_keys:
        return
    amount_in_cents = int(amount_in_cents)

    account_mapping = get_all_accounts_mapping(session)

    # User selects from account from list of active accounts
    print("Enter from account number: ")
    for i, account in account_mapping.items():
        print(f"({i}) {account.name}")
    from_account_id = input().strip()
    if from_account_id.lower() in exit_keys:
        return
    from_account = account_mapping.get(int(from_account_id), None)
    if not from_account:
        raise Exception("Invalid account selected!")
    from_account_name = from_account.name

    # Fetch from account
    from_account_obj: Account = (
        session.query(Account)
        .filter(Account.name == from_account_name.upper(), Account.is_active == True)
        .first()
    )

    # Validate from account and amount exceeds transfer amount
    if not from_account_obj:
        raise Exception(f"No active account found with name {from_account_name}!")
    if amount_in_cents > from_account_obj.value_in_cents:
        raise Exception(
            f"{amount_in_cents} greater than accounts value {from_account_obj.value_in_cents}!"
        )

    # User selects to account from list of active accounts
    print("Enter to account number: ")
    for i, account in account_mapping.items():
        print(f"({i}) {account.name}")
    to_account_id = input().strip()
    if to_account_id.lower() in exit_keys:
        return
    to_account = account_mapping.get(int(to_account_id), None)
    if not to_account:
        raise Exception("Invalid account selected!")
    to_account_name = to_account.name

    # Fetch to account
    to_account_obj: Account = (
        session.query(Account)
        .filter(Account.name == to_account_name.upper(), Account.is_active == True)
        .first()
    )

    # Validate to account
    if not to_account_obj:
        raise Exception(f"No active account found with name {to_account_name}!")

    # Perform transfer
    to_account_obj.value_in_cents += amount_in_cents
    from_account_obj.value_in_cents -= amount_in_cents
    session.commit()

    print(
        f"Successfully transferred {amount_in_cents} from {from_account_name} to {to_account_name}!"
    )


def create_credit_payment(
    session,
    amount_in_cents: int,
    credit_account_name: str,
    debit_account_name: str,
    description: str = None,
    date_of_transaction_str: str = None,
):
    """Creates a new credit payment."""
    credit_account: Account = (
        session.query(Account)
        .filter(Account.name == credit_account_name.upper(), Account.is_active == True)
        .first()
    )

    debit_account: Account = (
        session.query(Account)
        .filter(Account.name == debit_account_name.upper(), Account.is_active == True)
        .first()
    )

    try:
        if not credit_account:
            raise Exception(
                f"Credit account of name {credit_account_name} not found. Payment not processed"
            )
        if not debit_account:
            raise Exception(
                f"Debit account of name {debit_account_name} not found. Payment not processed"
            )

        date_of_transaction = None
        if not date_of_transaction_str:
            date_of_transaction = datetime.now(pacific_timezone).date()
        else:
            date_of_transaction = datetime.strptime(
                date_of_transaction_str, "%Y-%m-%d"
            ).date()

        new_payment = CreditPayment(
            amount_in_cents=amount_in_cents,
            credit_account_id=credit_account.id,
            description=description,
            date_of_transaction=date_of_transaction,
        )
        transaction_message = (
            f"Credit payment for {credit_account_name} on {date_of_transaction}"
        )

        session.add(new_payment)

        # Remove paid credit amount from credit bucket and deduct from debit
        create_transaction(
            session,
            amount_in_cents,
            TransactionType.CREDIT,
            transaction_message,
            credit_account.name,
        )
        create_transaction(
            session,
            amount_in_cents,
            TransactionType.DEBIT,
            transaction_message,
            debit_account.name,
        )
        print(
            f"Successfully create credit payment for {credit_account_name} and amount {amount_in_cents}\n{description}"
        )
    except:
        print(
            f"Could not create credit payment for {credit_account_name} and amount {amount_in_cents}"
        )


def _transfer(session):
    """Helper function to transfer amount from one account to another. Both accounts must be active."""
    pass
