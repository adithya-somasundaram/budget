"""Agent-facing tools.

Thin wrappers over the existing infra functions. Read tools run freely. Every
write tool is CONFIRM-GATED: it renders a summary table and requires an explicit
yes at the terminal before it touches the database, so a write can never happen
without the user seeing exactly what is about to change.
"""

from anthropic import beta_tool
from rich.console import Console

from app import session
from src.accounts.model import Account, AccountType
from src.accounts.services import adjust_account_value
from src.budget_categories.infra import create_budget_category, get_budget_leftover
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str
from src.transactions.infra import create_transaction
from src.transactions.model import TransactionDirection, TransactionType
from src.view_helpers import get_active_accounts, new_table

console = Console()


def _confirm(table, prompt="Apply these changes?") -> bool:
    """Prints a summary table and blocks for an explicit yes/no at the terminal."""
    console.print(table)
    answer = input(f"{prompt} (yes/no): ").strip().lower()
    return answer in ("y", "yes")


def _find_account(name: str) -> Account:
    return (
        session.query(Account)
        .filter(Account.name == name.upper(), Account.is_active == True)
        .first()
    )


def _find_budget_category(name: str) -> BudgetCategory:
    return (
        session.query(BudgetCategory)
        .filter(BudgetCategory.name == name.upper(), BudgetCategory.is_active == True)
        .first()
    )


# --------------------------------------------------------------------------- #
# Read tools (no confirmation)
# --------------------------------------------------------------------------- #
@beta_tool
def list_accounts() -> str:
    """List all active accounts with their type and current balance.

    Use this to resolve an account name the user mentions, to learn an account's
    type (which determines increment/decrement behaviour), and to check current
    balances. Credit-account balances represent what is owed.
    """
    accounts = get_active_accounts(session)
    if not accounts:
        return "No active accounts."
    lines = [
        f"{a.name} | type={a.type.value} | balance={cents_to_dollars_str(a.value_in_cents)}"
        for a in accounts
    ]
    return "\n".join(lines)


@beta_tool
def list_budget_categories() -> str:
    """List all active budget categories with their remaining amount, plus the
    current LEFTOVER (unbudgeted liquid cash). Use this to resolve a budget name
    the user mentions and to see current remaining amounts.
    """
    categories = (
        session.query(BudgetCategory)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )
    lines = [
        f"{c.name} | remaining={cents_to_dollars_str(c.amount_in_cents)}"
        for c in categories
    ]
    lines.append(f"LEFTOVER | {cents_to_dollars_str(get_budget_leftover(session))}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Write tools (confirm-gated)
# --------------------------------------------------------------------------- #
@beta_tool
def record_transactions(transactions: list[dict]) -> str:
    """Record one or more transactions, after showing the user a summary table and
    getting confirmation.

    Each item in `transactions` is an object with:
      - amount_cents (int, required): amount as a positive integer of cents, e.g. 4250 for $42.50.
      - account (str, required): the account name the transaction hits.
      - direction (str, optional): "decrement" (money leaving / spending, the default)
        or "increment" (money coming in, e.g. a paycheck or refund). Credit accounts
        are handled automatically: a decrement on a credit account raises what is owed.
      - type (str, optional): one of credit, debit, cash, check, venmo. If the account
        has an exclusive transaction type, that is used and this is ignored. Otherwise
        defaults to the account's type or debit.
      - description (str, required): short description of the transaction.
      - budget (str, optional): a budget category name to also apply this against.
      - date (str, optional): YYYY-MM-DD. Defaults to today when omitted.

    Call list_accounts / list_budget_categories first to resolve names and types.
    Returns a message stating whether the user confirmed and what was written.
    """
    staged = []
    for t in transactions:
        account = _find_account(t["account"])
        if not account:
            return f"No active account named '{t['account']}'. Nothing was written; ask the user to clarify."

        budget = None
        if t.get("budget"):
            budget = _find_budget_category(t["budget"])
            if not budget:
                return f"No active budget named '{t['budget']}'. Nothing was written; ask the user to clarify."

        direction = (
            TransactionDirection.INCREMENT
            if str(t.get("direction", "decrement")).lower() == "increment"
            else TransactionDirection.DECREMENT
        )

        if account.transaction_type:
            ttype = account.transaction_type
        elif t.get("type"):
            ttype = TransactionType[str(t["type"]).upper()]
        else:
            ttype = TransactionType[account.type.name] if account.type.name in TransactionType.__members__ else TransactionType.DEBIT

        staged.append(
            {
                "account": account,
                "amount_cents": int(t["amount_cents"]),
                "direction": direction,
                "type": ttype,
                "description": t.get("description", ""),
                "budget": budget,
                "date": t.get("date") or None,
            }
        )

    table = new_table("Date", "Account", "Dir", "Amount", "Type", "Description", "Budget")
    for s in staged:
        table.add_row(
            s["date"] or "today",
            s["account"].name,
            s["direction"].value,
            cents_to_dollars_str(s["amount_cents"]),
            s["type"].name.title(),
            s["description"],
            s["budget"].name if s["budget"] else "-",
        )

    if not _confirm(table, "Record these transactions?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        create_transaction(
            session,
            amount_in_cents=s["amount_cents"],
            transaction_type=s["type"],
            direction=s["direction"],
            description=s["description"],
            account_id=s["account"].id,
            budget_category_id=s["budget"].id if s["budget"] else None,
            date_of_transaction_str=s["date"],
        )
    return f"Confirmed. Recorded {len(staged)} transaction(s)."


@beta_tool
def adjust_accounts(adjustments: list[dict]) -> str:
    """Set the value of one or more accounts to a new absolute amount (useful for
    investment accounts whose value drifts), after showing a before/after table and
    getting confirmation.

    Each item in `adjustments` is an object with:
      - account (str, required): the account name.
      - new_amount_cents (int, required): the new absolute balance in cents.
      - reason (str, optional): why the value changed (e.g. "market gains").

    This records the difference as an ADJUSTMENT transaction under the hood.
    Returns a message stating whether the user confirmed.
    """
    staged = []
    for a in adjustments:
        account = _find_account(a["account"])
        if not account:
            return f"No active account named '{a['account']}'. Nothing was written; ask the user to clarify."
        staged.append(
            {
                "account": account,
                "old": account.value_in_cents,
                "new": int(a["new_amount_cents"]),
                "reason": a.get("reason") or "agent adjustment",
            }
        )

    table = new_table("Account", "Before", "After", "Reason", justify_first_right=False)
    for s in staged:
        table.add_row(
            s["account"].name,
            cents_to_dollars_str(s["old"]),
            cents_to_dollars_str(s["new"]),
            s["reason"],
        )

    if not _confirm(table, "Apply these account adjustments?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        adjust_account_value(session, s["account"].name, s["new"], reason=s["reason"])
    return f"Confirmed. Adjusted {len(staged)} account(s)."


@beta_tool
def set_budgets(budgets: list[dict]) -> str:
    """Create budget categories or set existing ones to a new absolute amount, after
    showing a before/after table and getting confirmation.

    Each item in `budgets` is an object with:
      - name (str, required): the budget category name.
      - new_amount_cents (int, required): the new absolute remaining amount in cents.

    A name that does not exist yet is created; an existing one is set to the new
    amount. Returns a message stating whether the user confirmed.
    """
    staged = []
    for b in budgets:
        existing = _find_budget_category(b["name"])
        staged.append(
            {
                "name": b["name"].upper(),
                "existing": existing,
                "old": existing.amount_in_cents if existing else None,
                "new": int(b["new_amount_cents"]),
            }
        )

    table = new_table("Budget", "Before", "After", justify_first_right=False)
    for s in staged:
        table.add_row(
            s["name"],
            cents_to_dollars_str(s["old"]) if s["existing"] else "(new)",
            cents_to_dollars_str(s["new"]),
        )

    if not _confirm(table, "Apply these budget changes?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        if s["existing"]:
            s["existing"].amount_in_cents = s["new"]
            session.commit()
        else:
            create_budget_category(session, s["name"], s["new"])
    return f"Confirmed. Set {len(staged)} budget(s)."


ALL_TOOLS = [
    list_accounts,
    list_budget_categories,
    record_transactions,
    adjust_accounts,
    set_budgets,
]
