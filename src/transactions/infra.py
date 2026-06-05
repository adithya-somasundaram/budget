from datetime import datetime

from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from src.accounts.model import Account, AccountType
from src.accounts.infra import get_liquid_total
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str, pacific_timezone, exit_keys
from src.transactions.model import Transaction, TransactionDirection, TransactionType


def make_summary_panel(session) -> Panel:
    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True)
        .order_by(Account.created_at)
        .all()
    )

    account_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    account_table.add_column("#", justify="right")
    account_table.add_column("Account")
    account_table.add_column("Balance", justify="right")

    grand_total = 0
    for i, account in enumerate(accounts, 1):
        is_credit = account.type == AccountType.CREDIT
        value_str = ("-" if is_credit else "") + cents_to_dollars_str(account.value_in_cents)
        account_table.add_row(str(i), account.name, value_str)
        grand_total += -account.value_in_cents if is_credit else account.value_in_cents
    account_table.add_section()
    account_table.add_row("", "[bold]TOTAL[/bold]", f"[bold]{cents_to_dollars_str(grand_total)}[/bold]")

    categories = (
        session.query(BudgetCategory.name, BudgetCategory.amount_in_cents)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name)
        .all()
    )

    budget_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    budget_table.add_column("#", justify="right")
    budget_table.add_column("Budget")
    budget_table.add_column("Remaining", justify="right")

    if categories:
        budget_total = 0
        for i, cat in enumerate(categories, 1):
            budget_table.add_row(str(i), cat.name, cents_to_dollars_str(cat.amount_in_cents))
            budget_total += cat.amount_in_cents
        liquid_total = get_liquid_total(session)
        leftover = liquid_total - budget_total
        budget_table.add_section()
        budget_table.add_row("", "[bold]LEFTOVER[/bold]", f"[bold]{cents_to_dollars_str(leftover)}[/bold]")

    type_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    type_table.add_column("#", justify="right")
    type_table.add_column("Type")
    for i, name in [(1, "Credit"), (2, "Debit"), (3, "Cash"), (4, "Check"), (5, "Venmo")]:
        type_table.add_row(str(i), name)
    type_table.add_section()
    type_table.add_row("[bold]Direction[/bold]", "")
    type_table.add_row("1", "Decrement")
    type_table.add_row("2", "Increment")

    return Panel(Columns([account_table, budget_table, type_table]), title="Summary")


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
