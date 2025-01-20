from datetime import date

from sqlalchemy.sql import func

from src.credit_payments.model import CreditSource
from src.transactions.model import Transaction, TransactionType


def create_new_transaction(
    session,
    amount_in_cents: int,
    type: TransactionType,
    description: str,
    credit_source: CreditSource = None,
):
    """Creates a transaction of type type. By default, transactions are stored as negative."""
    # Credit transactions require a source
    if type == TransactionType.CREDIT and not credit_source:
        print("Need to input credit source for credit transaction!")
        return
    elif type != TransactionType.CREDIT and credit_source:
        print(f"No credit source should be inputted for transaction type {type}")
        return

    new_transaction = Transaction(
        amount_in_cents=-amount_in_cents,
        type=type,
        description=description,
        credit_type=credit_source,
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


def cents_to_dollars_str(value):
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


def get_summary(session, from_date: date = None):
    """Sums and returns all transactions by type. Also calculates total net value."""
    totals = session.query(
        Transaction.type,
        func.sum(Transaction.amount_in_cents).label("amount_in_cents"),
    )

    if from_date:
        totals = totals.filter(func.DATE(Transaction.created_at) <= from_date)

    totals = totals.group_by(Transaction.type).all()
    output = ""
    grand_total = 0
    for total in totals:
        grand_total += total.amount_in_cents
        output += f"{total.type} : {cents_to_dollars_str(total.amount_in_cents)}\n"

    return f"{output}TOTAL: {cents_to_dollars_str(grand_total)}"


def get_all_transactions(session, from_date: date):
    transaction_groups = (
        session.query(
            func.DATE(Transaction.created_at),
            func.group_concat(
                Transaction.type.op("||")("/")
                .op("||")(Transaction.amount_in_cents)
                .op("||")("/")
                .op("||")(Transaction.description)
            ).label("transactions"),
        )
        .filter(func.DATE(Transaction.created_at) >= from_date)
        .group_by(func.DATE(Transaction.created_at))
    ).all()

    for group in transaction_groups:
        day, transactions_for_date = group[0], group[1].split(",")
        print(f"\n{day}")
        for tr in transactions_for_date:
            t_type, t_amount, t_description = tr.split("/")
            print(f"{t_type} \t{cents_to_dollars_str(int(t_amount))} \t{t_description}")
        print(f"\nTotals on {day}")
        print(get_summary(session, day))
