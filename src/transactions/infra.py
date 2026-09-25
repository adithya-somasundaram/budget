from datetime import date, datetime

from sqlalchemy.sql import func

from src.accounts.model import Account, AccountType
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str, pacific_timezone
from src.transactions.model import Transaction, TransactionDirection, TransactionType


def create_transaction(
    session,
    amount_in_cents: int,
    transaction_type: TransactionType,
    description: str,
    account_id: int,
    direction: TransactionDirection = TransactionDirection.DECREMENT,
    budget_category_id: int = None,
    date_of_transaction_str: str = None,
) -> None:
    date_of_transaction = None
    if not date_of_transaction_str:
        date_of_transaction = datetime.now(pacific_timezone).date()
    else:
        date_of_transaction = datetime.strptime(
            date_of_transaction_str, "%Y-%m-%d"
        ).date()

    account: Account = (
        session.query(Account)
        .filter(Account.id == account_id, Account.is_active == True)
        .first()
    )

    if not account:
        print(f"Account of id {account_id} not found. Payment not processed")
        return

    is_credit_account = account.type == AccountType.CREDIT
    if (direction == TransactionDirection.INCREMENT) != is_credit_account:
        account.value_in_cents += amount_in_cents
    else:
        account.value_in_cents -= amount_in_cents

    new_transaction = Transaction(
        amount_in_cents=amount_in_cents,
        type=transaction_type,
        direction=direction,
        description=description,
        account_id=account.id,
        date_of_transaction=date_of_transaction,
    )

    budget_category = None
    if budget_category_id:
        budget_category: BudgetCategory = (
            session.query(BudgetCategory)
            .filter(
                BudgetCategory.id == budget_category_id,
                BudgetCategory.is_active == True,
            )
            .first()
        )

        if budget_category:
            if direction == TransactionDirection.INCREMENT:
                budget_category.amount_in_cents += amount_in_cents
            else:
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


def transactions_text(session, from_date: date = None) -> str:
    """Builds the grouped-by-date transactions string from `from_date` onward
    (defaults to today). Returns the text so both the human CLI (which prints it)
    and the agent (which embeds it) share the same compute+format logic.
    """
    if from_date is None:
        from_date = datetime.now(pacific_timezone).date()

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

    output = ""
    for group in transaction_groups:
        day, transactions_for_date = group[0], group[1].split(",")
        output += f"\n{day}\n"

        day_total_in_cents = 0
        for tr in transactions_for_date:
            t_type, t_amount_in_cents, t_description = tr.split("/")
            amount_str = cents_to_dollars_str(int(t_amount_in_cents))
            output += "{0} \t{1:10} \t{2}\n".format(t_type, amount_str, t_description)
            day_total_in_cents += int(t_amount_in_cents)

        output += f"Total spent on {day}: {cents_to_dollars_str(day_total_in_cents)}\n"

    return output.rstrip("\n")
