from datetime import date, datetime

from sqlalchemy.sql import func

from src.helpers import cents_to_dollars_str, pacific_timezone, exit_keys
from src.transactions.model import Transaction
from src.transactions.infra import create_transaction_input_helper


def get_all_transactions(
    session, from_date: date = datetime.now(pacific_timezone).date()
):
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
            amount_str = cents_to_dollars_str(abs(int(t_amount_in_cents)))
            print("{0} \t{1:10} \t{2}".format(t_type, amount_str, t_description))
            day_total_in_cents += abs(int(t_amount_in_cents))

        print(f"Total spent on {day}: {cents_to_dollars_str(day_total_in_cents)}")


def bulk_create_transactions(session):
    """Bulk creates transactions. Transactions should be in the format of create_transaction input"""
    from src.accounts.infra import get_all_accounts_mapping
    from src.budget_categories.infra import get_budget_category_mapping

    print(
        "Lets create some transactions! Enter 'quit' or 'exit' at any time to save and exit."
    )

    date_of_transaction_str = input(
        "Enter date of transaction in format YYYY-MM-DD, click 'Enter' to set to today: "
    ).strip()

    if date_of_transaction_str.lower() in exit_keys:
        return

    still_creating = True

    account_mapping = get_all_accounts_mapping(session)
    account_input_prompt = f"Enter transaction account number: "
    for i, account in account_mapping.items():
        account_input_prompt += f"\n({i}) {account.name}"

    budget_category_mapping = get_budget_category_mapping(session)
    budget_category_input_prompt = (
        f"Enter transaction budget category number, click 'Enter' to skip: "
    )
    for i, budget_category_name in budget_category_mapping.items():
        budget_category_input_prompt += f"\n({i}) {budget_category_name}"

    while still_creating:
        still_creating = create_transaction_input_helper(
            session,
            date_of_transaction_str,
            account_mapping,
            account_input_prompt,
            budget_category_mapping,
            budget_category_input_prompt,
        )


def create_transaction_input(session):
    """Creates transactions via user input. Transaction should be in the format of create_transaction input"""
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
    for i, budget_category_name in budget_category_mapping.items():
        budget_category_input_prompt += f"\n({i}) {budget_category_name}"

    create_transaction_input_helper(
        session,
        date_of_transaction_str,
        account_mapping,
        account_input_prompt,
        budget_category_mapping,
        budget_category_input_prompt,
    )
