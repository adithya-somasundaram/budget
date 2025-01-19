from sqlalchemy.sql import func

from app import db
from models import CreditPayment, CreditSource, Transaction, TransactionType

session = db.session


def create_new_transaction(
    amount_in_cents: int, type: TransactionType, description: str
):
    """Creates a transaction of type type. By default, transactions are stored as negative."""
    new_transaction = Transaction(
        amount_in_cents=-amount_in_cents, type=type, description=description
    )
    try:
        session.add(new_transaction)
        session.commit()
        print(
            "Successfully created transaction of type "
            + str(type)
            + " and amount "
            + str(amount_in_cents)
            + "\n"
            + description
        )
    except:
        print(
            "Could not create transaction of type "
            + str(type)
            + " and amount "
            + str(amount_in_cents)
        )


def create_new_credit_payment(amount_in_cents: int, type: CreditSource, description):
    """Creates a new credit payment."""
    new_payment = CreditPayment(
        amount_in_cents=amount_in_cents, credit_type=type, description=description
    )
    try:
        session.add(new_payment)
        session.commit()
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


def print_cents_in_dollars(value):
    """Default printing function. Input value in cents"""
    amount = value
    if amount < 0:
        amount = amount * -1
    dollars = int(amount / 100)
    cents = amount % 100

    if cents < 10:
        cents = "0" + str(cents)
    else:
        cents = str(cents)

    dollar_output = ""

    while dollars > 0:
        dollar_temp = dollars % 1000
        dollars = int(dollars / 1000)

        if dollars > 0:
            if dollar_temp < 10:
                dollar_temp = "00" + str(dollar_temp)
            elif dollar_temp < 100:
                dollar_temp = "0" + str(dollar_temp)

        dollar_output = str(dollar_temp) + dollar_output

        if dollars > 0:
            dollar_output = "," + dollar_output

    return (
        ("-" if value < 0 else "")
        + "$"
        + (dollar_output if len(dollar_output) > 0 else "0")
        + "."
        + cents
    )


def get_summary():
    """Sums and returns all transactions by type. Also calculates total net value."""
    totals = (
        session.query(
            Transaction.type,
            func.sum(Transaction.amount_in_cents).label("amount_in_cents"),
        )
        .group_by(Transaction.type)
        .all()
    )

    grand_total = 0
    for total in totals:
        grand_total += total.amount_in_cents
        print(str(total.type) + ": " + print_cents_in_dollars(total.amount_in_cents))

    print("TOTAL: " + print_cents_in_dollars(grand_total))
