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
from src.accounts.infra import create_new_account
from src.accounts.services import adjust_account_value, update_account
from src.budget_categories.infra import create_budget_category, get_budget_leftover
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str
from src.transactions.infra import create_transaction
from src.transactions.model import TransactionDirection, TransactionType
from src.transfers.infra import transfer
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
def create_accounts(accounts: list[dict]) -> str:
    """Create one or more new accounts, after showing a summary table and getting
    confirmation.

    Each item in `accounts` is an object with:
      - name (str, required): the account name (stored uppercase).
      - type (str, required): one of credit, debit, cash, check, venmo, investing.
      - value_cents (int, optional): the starting balance in cents. Defaults to 0.
        For a credit account this is what is currently owed.
      - transaction_type (str, optional): pins the account to an exclusive transaction
        type (credit, debit, cash, check, venmo) so future transactions on it don't
        need one specified. Usually omitted.

    Call list_accounts first to avoid creating a duplicate of an existing account.
    Returns a message stating whether the user confirmed.
    """
    staged = []
    for a in accounts:
        try:
            acct_type = AccountType[str(a["type"]).upper()]
        except KeyError:
            return f"'{a.get('type')}' is not a valid account type (credit, debit, cash, check, venmo, investing). Nothing was written; ask the user to clarify."

        ttype = None
        if a.get("transaction_type"):
            try:
                ttype = TransactionType[str(a["transaction_type"]).upper()]
            except KeyError:
                return f"'{a['transaction_type']}' is not a valid transaction type. Nothing was written; ask the user to clarify."

        staged.append(
            {
                "name": a["name"].upper(),
                "type": acct_type,
                "value": int(a.get("value_cents") or 0),
                "ttype": ttype,
            }
        )

    table = new_table("Account", "Type", "Starting Balance", "Txn Type", justify_first_right=False)
    for s in staged:
        table.add_row(
            s["name"],
            s["type"].value,
            cents_to_dollars_str(s["value"]),
            s["ttype"].name.title() if s["ttype"] else "-",
        )

    if not _confirm(table, "Create these accounts?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        create_new_account(session, s["name"], s["type"], s["value"], s["ttype"])
    return f"Confirmed. Created {len(staged)} account(s)."


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
def update_accounts(updates: list[dict]) -> str:
    """Change an account's name, type, and/or exclusive transaction type (NOT its
    value — use adjust_accounts for that), after showing a before/after table and
    getting confirmation.

    Each item in `updates` is an object with:
      - account (str, required): the current account name.
      - new_name (str, optional): rename the account to this.
      - new_type (str, optional): change the account type to one of credit, debit,
        cash, check, venmo, investing. Note this changes how the account counts
        toward totals (credit balances are subtracted).
      - new_transaction_type (str, optional): change the exclusive transaction type
        to one of credit, debit, cash, check, venmo.

    Only the fields you provide are changed. Call list_accounts first to resolve the
    current name. Returns a message stating whether the user confirmed.
    """
    staged = []
    for u in updates:
        account = _find_account(u["account"])
        if not account:
            return f"No active account named '{u['account']}'. Nothing was written; ask the user to clarify."

        new_type = None
        if u.get("new_type"):
            try:
                new_type = AccountType[str(u["new_type"]).upper()]
            except KeyError:
                return f"'{u['new_type']}' is not a valid account type (credit, debit, cash, check, venmo, investing). Nothing was written; ask the user to clarify."

        new_ttype = None
        if u.get("new_transaction_type"):
            try:
                new_ttype = TransactionType[str(u["new_transaction_type"]).upper()]
            except KeyError:
                return f"'{u['new_transaction_type']}' is not a valid transaction type. Nothing was written; ask the user to clarify."

        staged.append(
            {
                "account": account,
                "new_name": u["new_name"].upper() if u.get("new_name") else None,
                "new_type": new_type,
                "new_ttype": new_ttype,
            }
        )

    table = new_table("Account", "Name", "Type", "Txn Type", justify_first_right=False)
    for s in staged:
        acct = s["account"]
        old_ttype = acct.transaction_type.name.title() if acct.transaction_type else "-"
        new_ttype = s["new_ttype"].name.title() if s["new_ttype"] else old_ttype
        table.add_row(
            acct.name,
            s["new_name"] or acct.name,
            (s["new_type"] or acct.type).value,
            new_ttype,
        )

    if not _confirm(table, "Apply these account updates?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        try:
            update_account(
                session,
                s["account"].name,
                new_name=s["new_name"],
                new_type=s["new_type"],
                new_transaction_type=s["new_ttype"],
            )
        except Exception as e:
            session.rollback()
            return f"Update failed: {e}. Some changes may not have been applied; ask the user how to proceed."
    return f"Confirmed. Updated {len(staged)} account(s)."


@beta_tool
def pay_credit(payments: list[dict]) -> str:
    """Pay down a credit account from a paying (non-credit) account, after showing a
    before/after table and getting confirmation. This is a two-sided transfer: it
    lowers the paying account's balance AND lowers what is owed on the credit account,
    and is logged in the transfer ledger (NOT as a spending transaction).

    Use this whenever the user says they paid a credit card / paid down a balance.
    Do NOT use record_transactions for a credit payment — that would only touch one
    account and leave the card unpaid.

    Each item in `payments` is an object with:
      - credit_account (str, required): the credit account being paid off.
      - paying_account (str, required): the non-credit account the money comes from.
      - amount_cents (int, required): the payment amount in cents. Must not exceed
        what is currently owed on the credit account.

    Call list_accounts first to resolve names and confirm which is the credit account.
    Returns a message stating whether the user confirmed.
    """
    staged = []
    for p in payments:
        credit = _find_account(p["credit_account"])
        if not credit:
            return f"No active account named '{p['credit_account']}'. Nothing was written; ask the user to clarify."
        if credit.type != AccountType.CREDIT:
            return f"'{credit.name}' is not a credit account, so it can't be paid off this way. Nothing was written; ask the user to clarify."

        paying = _find_account(p["paying_account"])
        if not paying:
            return f"No active account named '{p['paying_account']}'. Nothing was written; ask the user to clarify."
        if paying.type == AccountType.CREDIT:
            return f"'{paying.name}' is a credit account and can't be the paying account. Nothing was written; ask the user to clarify."

        amount = int(p["amount_cents"])
        if amount > credit.value_in_cents:
            return f"Payment of {cents_to_dollars_str(amount)} exceeds the {cents_to_dollars_str(credit.value_in_cents)} owed on {credit.name}. Nothing was written; ask the user to confirm the amount."

        staged.append({"credit": credit, "paying": paying, "amount": amount})

    table = new_table("Amount", "Credit (owed)", "Paying", justify_first_right=False)
    for s in staged:
        credit_after = s["credit"].value_in_cents - s["amount"]
        paying_after = s["paying"].value_in_cents - s["amount"]
        table.add_row(
            cents_to_dollars_str(s["amount"]),
            f"{s['credit'].name}: {cents_to_dollars_str(s['credit'].value_in_cents)} -> {cents_to_dollars_str(credit_after)}",
            f"{s['paying'].name}: {cents_to_dollars_str(s['paying'].value_in_cents)} -> {cents_to_dollars_str(paying_after)}",
        )

    if not _confirm(table, "Make these credit payments?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        try:
            transfer(
                session,
                s["credit"].id,
                s["paying"].id,
                s["amount"],
                f"Credit payment from {s['credit'].name} to {s['paying'].name}",
            )
        except Exception as e:
            session.rollback()
            return f"Credit payment failed: {e}. Some payments may not have been applied; ask the user how to proceed."
    return f"Confirmed. Made {len(staged)} credit payment(s)."


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
    create_accounts,
    adjust_accounts,
    update_accounts,
    pay_credit,
    set_budgets,
]
