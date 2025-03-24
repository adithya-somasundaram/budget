from datetime import date

from src.accounts.model import Account
from src.credit_payments.model import CreditPayment
from src.transactions.model import TransactionType
from src.transactions.services import create_new_transaction


def create_new_credit_payment(
    session, amount_in_cents: int, account_name: str, description
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

        new_payment = CreditPayment(
            amount_in_cents=amount_in_cents,
            credit_account_id=credit_account.id,
            description=description,
        )
        today = date.today()
        transaction_message = f"Credit payment for {account_name} on {today}"

        session.add(new_payment)

        # Remove paid credit amount from credit bucket and deduct from debit
        create_new_transaction(
            session, -amount_in_cents, TransactionType.CREDIT, transaction_message, type
        )
        create_new_transaction(
            session, amount_in_cents, TransactionType.DEBIT, transaction_message
        )
        print(
            "Successfully create credit payment for "
            + account_name
            + " and amount "
            + str(amount_in_cents)
            + "\n"
            + description
        )
    except:
        print(
            "Could not create credit payment for "
            + account_name
            + " and amount "
            + str(amount_in_cents)
        )
