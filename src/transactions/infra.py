from datetime import datetime

from src.accounts.model import Account
from src.budget_categories.model import BudgetCategory
from src.helpers import pacific_timezone
from src.transactions.model import Transaction, TransactionType


def create_transaction_input_helper(
    session,
    date_of_transaction,
    account_mapping: dict[int, Account],
    account_input_prompt: str,
    budget_category_mapping: dict[int, str],
    budget_category_input_prompt: str,
):
    """Prompts user for transaction parameters and creates single transaction"""

    # Get transaction amount in cents
    transaction_amount = input(
        "Enter transaction amount in cents (e.g. 1050 for $10.50): "
    ).strip()
    if transaction_amount.lower() == "quit":
        return False
    transaction_amount = int(transaction_amount)

    # Get transaction account
    print(account_input_prompt)
    transaction_account_number = input().strip()
    if transaction_account_number.lower() == "quit":
        return False
    transaction_account = account_mapping.get(int(transaction_account_number), None)

    # Get transaction type
    transaction_type = None
    if transaction_account.transaction_type:
        transaction_type = transaction_account.transaction_type
    else:
        transaction_type = (
            input(
                "Enter transaction type number:\n(1) Credit\n(2) Debit\n(3) Cash\n(4) Check\n(5) Venmo\n"
            )
            .strip()
            .upper()
        )
        if transaction_type.lower() == "quit":
            return False
        transaction_type = TransactionType(int(transaction_type))

    # Get transaction description, can be blank
    transaction_description = input("Enter transaction description: ").strip()
    if transaction_description.lower() == "quit":
        return False

    # Get transaction budget category if budgets exist, can be blank
    transaction_budget_category_name = None
    if len(budget_category_mapping.values()):
        print(budget_category_input_prompt)
        transaction_budget_category_name = input().strip()
        if transaction_budget_category_name.lower() == "quit":
            return False
        transaction_budget_category_name = (
            budget_category_mapping.get(int(transaction_budget_category_name), None)
            if transaction_budget_category_name
            else None
        )

    try:
        create_transaction(
            session,
            amount_in_cents=transaction_amount,
            transaction_type=transaction_type,
            description=transaction_description,
            account_name=transaction_account.name,
            budget_category_name=transaction_budget_category_name,
            date_of_transaction_str=(
                date_of_transaction if date_of_transaction != "" else None
            ),
        )
        return True
    except Exception as e:
        print(f"Error creating new transaction: {str(e)}")
        session.rollback()
        return True


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
