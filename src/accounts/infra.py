from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from src.accounts.model import Account, AccountType
from src.transactions.model import TransactionType


def make_summary_panel(session) -> Panel:
    from src.budget_categories.model import BudgetCategory
    from src.helpers import cents_to_dollars_str

    accounts: list[Account] = (
        session.query(Account.name, Account.value_in_cents, Account.type)
        .filter(Account.is_active == True)
        .order_by(Account.created_at)
        .all()
    )

    account_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    account_table.add_column("Account")
    account_table.add_column("Balance", justify="right")

    grand_total = 0
    for account in accounts:
        is_credit = account.type == AccountType.CREDIT
        value_str = ("-" if is_credit else "") + cents_to_dollars_str(account.value_in_cents)
        account_table.add_row(account.name, value_str)
        grand_total += -account.value_in_cents if is_credit else account.value_in_cents
    account_table.add_section()
    account_table.add_row("[bold]TOTAL[/bold]", f"[bold]{cents_to_dollars_str(grand_total)}[/bold]")

    categories = (
        session.query(BudgetCategory.name, BudgetCategory.amount_in_cents)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name)
        .all()
    )

    budget_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    budget_table.add_column("Budget")
    budget_table.add_column("Remaining", justify="right")

    if categories:
        budget_total = 0
        for cat in categories:
            budget_table.add_row(cat.name, cents_to_dollars_str(cat.amount_in_cents))
            budget_total += cat.amount_in_cents
        liquid_total = get_liquid_total(session)
        leftover = liquid_total - budget_total
        budget_table.add_section()
        budget_table.add_row("[bold]LEFTOVER[/bold]", f"[bold]{cents_to_dollars_str(leftover)}[/bold]")

    return Panel(Columns([account_table, budget_table]), title="Summary")


def get_all_accounts_mapping(
    session, account_type: AccountType = None
) -> dict[int, Account]:
    """Returns dict mapping an integer to and account. Good for user input."""
    query = session.query(Account.id, Account.name, Account.transaction_type).filter(
        Account.is_active == True
    )
    if account_type:
        query = query.filter(Account.type == account_type)
    accounts: list[Account] = query.order_by(Account.created_at).all()

    return {i: account for i, account in enumerate(accounts, 1)}


def get_liquid_total(session) -> int:
    """Returns total liquid assets in cents, excluding investing accounts. Credit accounts are subtracted."""
    accounts: list[Account] = (
        session.query(Account.value_in_cents, Account.type)
        .filter(Account.is_active == True, Account.type != AccountType.INVESTING)
        .all()
    )
    total = 0
    for account in accounts:
        if account.type == AccountType.CREDIT:
            total -= account.value_in_cents
        else:
            total += account.value_in_cents
    return total


def create_new_account(
    session,
    name: str,
    account_type: AccountType,
    value_in_cents: int = None,
    transaction_type: TransactionType = None,
) -> int:
    """Creates a new account with given name and type. Returns new account id."""
    # dupe check
    dupe: Account = (
        session.query(Account)
        .filter(Account.name == name.upper(), Account.type == account_type)
        .first()
    )

    if dupe and dupe.is_active:
        raise Exception(
            f"Duplicate account with type {account_type} and name {name}! Id: {dupe.id}"
        )
    elif dupe:
        dupe.is_active = True
        dupe.value_in_cents = value_in_cents or 0
        session.commit()
        return

    new_account = Account(
        name=name.upper(),
        type=account_type,
        value_in_cents=value_in_cents or 0,
        is_active=True,
        transaction_type=transaction_type,
    )

    session.add(new_account)
    session.commit()

    print(
        f"New Account created with name {name} and type {account_type}: {new_account.id}"
    )
    return new_account.id
