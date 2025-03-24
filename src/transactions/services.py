from datetime import date

from sqlalchemy.sql import func

from src.accounts.model import Account, AccountType
from src.transactions.model import Transaction, TransactionType


def create_new_transaction(
    session,
    amount_in_cents: int,
    type: TransactionType,
    description: str,
    account_name: str = None,
):
    """Creates a transaction of type type. By default, transactions are stored as negative."""
    # Credit transactions require a source
    if type == TransactionType.CREDIT and not account_name:
        print("Need to input credit account for credit transaction!")
        return

    account: Account = (
        session.query(Account)
        .filter(Account.name == account_name.upper(), Account.is_active == True)
        .first()
    )

    if not account:
        print(f"Account of name {account_name} not found. Payment not processed")
        return

    new_transaction = Transaction(
        amount_in_cents=-amount_in_cents,
        type=type,
        description=description,
        account_id=account.id,
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


def get_all_transactions(session, from_date: date):
    """Gets and groups all transactions by date. Prints each days transactions along with summary from that date"""
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
            amount_str = cents_to_dollars_str(int(t_amount))
            print("{0} \t{1:10} \t{2}".format(t_type, amount_str, t_description))

        print(f"\nTotals on {day}")
        print(get_summary(session, day))
