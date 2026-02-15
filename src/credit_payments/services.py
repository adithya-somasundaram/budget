from datetime import date, datetime

import pytz

from src.accounts.model import Account
from src.credit_payments.model import CreditPayment
from src.transactions.model import TransactionType
from src.transactions.services import create_new_transaction


def create_new_credit_payment(
    session,
    amount_in_cents: int,
    account_name: str,
    description: str = None,
    date_of_transaction_str: str = None,
):
    """Creates a new credit payment."""
    credit_account: Account = (
        session.query(Account)
        .filter(Account.name == account_name.upper(), Account.is_active == True)
        .first()
    )

    try:
        if not credit_account:
            raise Exception(
                f"Account of name {account_name} not found. Payment not processed"
            )

        date_of_transaction = None
        if not date_of_transaction_str:
            pacific_timezone = pytz.timezone("America/Los_Angeles")
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
        today = date.today()
        transaction_message = f"Credit payment for {account_name} on {today}"

        session.add(new_payment)

        # Remove paid credit amount from credit bucket and deduct from debit
        create_new_transaction(
            session,
            -amount_in_cents,
            TransactionType.CREDIT,
            transaction_message,
            credit_account.name,
        )
        create_new_transaction(
            session,
            amount_in_cents,
            TransactionType.DEBIT,
            transaction_message,
            credit_account.name,
        )
        print(
            f"Successfully create credit payment for {account_name} and amount {amount_in_cents}\n{description}"
        )
    except:
        print(
            f"Could not create credit payment for {account_name} and amount {amount_in_cents}"
        )
