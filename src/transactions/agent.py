"""Agent-facing tool for transactions.

record_transactions is CONFIRM-GATED via _confirm: it renders a summary table and
requires an explicit yes at the terminal before writing. It resolves account and
budget names via the shared infra getters.
"""

from anthropic import beta_tool

from app import session
from src.accounts.infra import get_active_account_by_name
from src.agent.helpers import _confirm
from src.budget_categories.infra import get_active_budget_category_by_name
from src.helpers import cents_to_dollars_str
from src.transactions.infra import create_transaction
from src.transactions.model import TransactionDirection, TransactionType
from src.view_helpers import new_table


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
        account = get_active_account_by_name(session, t["account"])
        if not account:
            return f"No active account named '{t['account']}'. Nothing was written; ask the user to clarify."

        budget = None
        if t.get("budget"):
            budget = get_active_budget_category_by_name(session, t["budget"])
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
