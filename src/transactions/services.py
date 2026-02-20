from datetime import date, datetime

from sqlalchemy.sql import func

from src.accounts.model import Account
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str, pacific_timezone
from src.transactions.model import Transaction, TransactionType


def create_transaction(
    session,
    amount_in_cents: int,
    transaction_type: TransactionType,
    description: str,
    account_name: str,
    budget_category_name: str = None,
    date_of_transaction_str: str = None,
):
    """Creates a transaction of type type. By default, transactions are stored as negative."""

    date_of_transaction = None
    if not date_of_transaction_str:
        date_of_transaction = datetime.now(pacific_timezone).date()
    else:
        date_of_transaction = datetime.strptime(
            date_of_transaction_str, "%Y-%m-%d"
        ).date()

    # Credit transactions require a source
    if transaction_type == TransactionType.CREDIT and not account_name:
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

    if transaction_type == TransactionType.CREDIT:
        account.value_in_cents += amount_in_cents
    else:
        account.value_in_cents -= amount_in_cents

    new_transaction = Transaction(
        amount_in_cents=-amount_in_cents,
        type=transaction_type,
        description=description,
        account_id=account.id,
        date_of_transaction=date_of_transaction,
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
            f"Successfully created transaction of type {str(transaction_type)} and amount {str(amount_in_cents)}\n {description}"
        )
        if budget_category:
            print(
                f"Budget {budget_category.name} now {budget_category.amount_in_cents}"
            )
        else:
            print("No budget adjusted.")

    except:
        print(
            f"Could not create transaction of type {str(transaction_type)} and amount {str(amount_in_cents)}"
        )


def get_all_transactions(session, from_date: date):
    """Gets and groups all transactions by date. Prints each days transactions along with summary from that date"""
    transaction_groups = (
        session.query(
            Transaction.date_of_transaction,
            func.group_concat(
                Transaction.type.op("||")("/")
                .op("||")(Transaction.amount_in_cents)
                .op("||")("/")
                .op("||")(Transaction.description)
            ).label("transactions"),
        )
        .filter(Transaction.date_of_transaction >= from_date)
        .group_by(Transaction.date_of_transaction)
    ).all()

    for group in transaction_groups:
        day, transactions_for_date = group[0], group[1].split(",")
        print(f"\n{day}")

        for tr in transactions_for_date:
            t_type, t_amount, t_description = tr.split("/")
            amount_str = cents_to_dollars_str(int(t_amount))
            print("{0} \t{1:10} \t{2}".format(t_type, amount_str, t_description))

        print(f"\nTotals on {day}")


def bulk_create_transactions(session):
    """Bulk creates transactions. Transactions should be in the format of create_transaction input"""
    print("Lets create some transactions! Enter 'quit' at any time to save and exit.")

    date_of_transaction_str = input(
        "Enter date of transaction in format YYYY-MM-DD, click 'Enter' to set to today: "
    ).strip()

    if date_of_transaction_str.lower() == "quit":
        return

    still_creating = True

    while still_creating:
        still_creating = create_transaction_input_helper(
            session, date_of_transaction_str
        )


def create_transaction_input(session):
    """Creates transactions via user input. Transaction should be in the format of create_transaction input"""

    date_of_transaction_str = input(
        "Enter date of transaction in format YYYY-MM-DD, click 'Enter' to set to today: "
    ).strip()

    create_transaction_input_helper(session, date_of_transaction_str)


def create_transaction_input_helper(session, date_of_transaction):
    transaction_amount = input(
        "Enter transaction amount in cents (e.g. 1050 for $10.50): "
    ).strip()
    if transaction_amount.lower() == "quit":
        return False

    transaction_type = (
        input("Enter transaction type (CREDIT, DEBIT, CASH, CHECK, VENMO): ")
        .strip()
        .upper()
    )
    if transaction_type.lower() == "quit":
        return False

    transaction_description = input("Enter transaction description: ").strip()
    if transaction_description.lower() == "quit":
        return False

    transaction_account_name = input("Enter transaction account name: ").strip()
    if transaction_account_name.lower() == "quit":
        return False

    transaction_budget_category_name = input(
        "Enter transaction budget category to deduct from (optional): "
    ).strip()
    if transaction_budget_category_name.lower() == "quit":
        return False

    try:
        create_transaction(
            session,
            amount_in_cents=int(transaction_amount),
            type=TransactionType[transaction_type],
            description=transaction_description,
            account_name=transaction_account_name,
            budget_category_name=(
                transaction_budget_category_name
                if transaction_budget_category_name != ""
                else None
            ),
            date_of_transaction_str=(
                date_of_transaction if date_of_transaction != "" else None
            ),
        )
        return True
    except Exception as e:
        print(f"Error creating new transaction: {str(e)}")
        session.rollback()
        return True
