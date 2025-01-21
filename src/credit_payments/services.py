from datetime import date

from src.credit_payments.model import CreditPayment, CreditSource
from src.transactions.model import TransactionType
from src.transactions.services import create_new_transaction


def create_new_credit_payment(
    session, amount_in_cents: int, type: CreditSource, description
):
    """Creates a new credit payment."""
    new_payment = CreditPayment(
        amount_in_cents=amount_in_cents, credit_type=type, description=description
    )
    today = date.today()
    transaction_message = f"Credit payment for {type} on {today}"
    try:
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
            + str(type)
            + " and amount "
            + str(amount_in_cents)
            + "\n"
            + description
        )
    except:
        print(
            "Could not create credit payment for "
            + str(type)
            + " and amount "
            + str(amount_in_cents)
        )
