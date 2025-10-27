from datetime import date

from sqlalchemy.sql import func

from src.accounts.model import Account
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str
from src.transactions.model import Transaction, TransactionType


def create_new_transaction(
    session,
    amount_in_cents: int,
    type: TransactionType,
    description: str,
    account_name: str,
    budget_category_name: str = None,
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

    budget_category = None
    if budget_category_name:
        budget_category: BudgetCategory = (
            session.query(BudgetCategory)
            .filter(
                BudgetCategory.name == budget_category_name.upper(),
                BudgetCategory.is_active == True,
            )
            .first()
        )

        if budget_category:
            budget_category.amount_in_cents -= amount_in_cents

    try:
        session.add(new_transaction)
        session.commit()
        print(
            f"Successfully created transaction of type {str(type)}  and amount {str(amount_in_cents)}\n {description}"
        )
        if budget_category:
            print(
                f"Budget {budget_category.name} now {budget_category.amount_in_cents}"
            )
        else:
            print("No budget adjusted.")

    except:
        print(
            f"Could not create transaction of type {str(type)} and amount {str(amount_in_cents)}"
        )


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
