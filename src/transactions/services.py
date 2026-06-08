from datetime import date, datetime

from sqlalchemy.sql import func

from src.accounts.model import Account
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str, pacific_timezone, exit_keys
from src.transactions.infra import create_transaction
from src.transactions.model import Transaction, TransactionDirection, TransactionType


def create_transaction_input_helper(
    session,
    date_of_transaction,
    account_mapping: dict[int, Account],
    account_input_prompt: str,
    budget_category_mapping: dict[int, BudgetCategory],
    budget_category_input_prompt: str,
) -> bool:
    """Prompts user for transaction parameters and creates single transaction. Returns false if user exits out of transaction creation, true if transaction created or error occurred."""

    transaction_amount = input(
        "Enter transaction amount in cents (e.g. 1050 for $10.50): "
    ).strip()
    if transaction_amount.lower() in exit_keys:
        return False
    transaction_amount = int(transaction_amount)

    transaction_account_number = input(account_input_prompt).strip()
    if transaction_account_number.lower() in exit_keys:
        return False
    transaction_account = account_mapping.get(int(transaction_account_number), None)
    if not transaction_account:
        print("Invalid account selected!")
        return True

    transaction_type = None
    if transaction_account.transaction_type:
        transaction_type = transaction_account.transaction_type
    else:
        transaction_type_input = input("Enter transaction type number: ").strip()
        if transaction_type_input.lower() in exit_keys:
            return False
        transaction_type = TransactionType(int(transaction_type_input))

    direction_input = input(
        "Enter direction (1/2, default 1): "
    ).strip()
    if direction_input.lower() in exit_keys:
        return False
    transaction_direction = (
        TransactionDirection.INCREMENT if direction_input == "2" else TransactionDirection.DECREMENT
    )

    transaction_description = input("Enter transaction description: ").strip()
    if transaction_description.lower() in exit_keys:
        return False

    transaction_budget_category = None
    if len(budget_category_mapping.values()):
        transaction_budget_category = input(budget_category_input_prompt).strip()
        if transaction_budget_category.lower() in exit_keys:
            return False
        transaction_budget_category = (
            budget_category_mapping.get(int(transaction_budget_category), None)
            if transaction_budget_category != ""
            else None
        )

    try:
        create_transaction(
            session,
            amount_in_cents=transaction_amount,
            transaction_type=transaction_type,
            direction=transaction_direction,
            description=transaction_description,
            account_id=transaction_account.id,
            budget_category_id=(
                transaction_budget_category.id if transaction_budget_category else None
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


def view_all_transactions(
    session, from_date: date = datetime.now(pacific_timezone).date()
) -> None:
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

        day_total_in_cents = 0
        for tr in transactions_for_date:
            t_type, t_amount_in_cents, t_description = tr.split("/")
            amount_str = cents_to_dollars_str(int(t_amount_in_cents))
            print("{0} \t{1:10} \t{2}".format(t_type, amount_str, t_description))
            day_total_in_cents += int(t_amount_in_cents)

        print(f"Total spent on {day}: {cents_to_dollars_str(day_total_in_cents)}")


def bulk_create_transactions(session) -> None:
    """Bulk creates transactions. Transactions should be in the format of create_transaction input"""
    from rich.console import Console
    from src.accounts.infra import get_all_accounts_mapping
    from src.transactions.view import make_summary_panel
    from src.budget_categories.infra import get_budget_category_mapping

    print(
        "Lets create some transactions! Enter 'quit' or 'exit' at any time to save and exit."
    )

    date_of_transaction_str = input(
        "Enter date of transaction in format YYYY-MM-DD, click 'Enter' to set to today: "
    ).strip()

    if date_of_transaction_str.lower() in exit_keys:
        return

    account_mapping = get_all_accounts_mapping(session)
    account_input_prompt = "Enter account number: "

    budget_category_mapping = get_budget_category_mapping(session)
    budget_category_input_prompt = "Enter budget number (or Enter to skip): "

    console = Console()
    still_creating = True
    while still_creating:
        console.clear()
        console.print(make_summary_panel(session))
        still_creating = create_transaction_input_helper(
            session,
            date_of_transaction_str,
            account_mapping,
            account_input_prompt,
            budget_category_mapping,
            budget_category_input_prompt,
        )


### Deprecated functions below, kept for reference, may be deleted in the future ###
def create_transaction_input(session) -> None:
    """Creates single transaction via user input. Transaction should be in the format of create_transaction input"""
    from src.accounts.infra import get_all_accounts_mapping
    from src.budget_categories.infra import get_budget_category_mapping

    date_of_transaction_str = input(
        "Enter date of transaction in format YYYY-MM-DD, click 'Enter' to set to today: "
    ).strip()

    account_mapping = get_all_accounts_mapping(session)
    account_input_prompt = f"Enter transaction account number: "
    for i, account in account_mapping.items():
        account_input_prompt += f"\n({i}) {account.name}"

    budget_category_mapping = get_budget_category_mapping(session)
    budget_category_input_prompt = (
        f"Enter transaction budget category number, click 'Enter' to skip: "
    )
    for i, budget_category in budget_category_mapping.items():
        budget_category_input_prompt += f"\n({i}) {budget_category.name}"

    create_transaction_input_helper(
        session,
        date_of_transaction_str,
        account_mapping,
        account_input_prompt,
        budget_category_mapping,
        budget_category_input_prompt,
    )
