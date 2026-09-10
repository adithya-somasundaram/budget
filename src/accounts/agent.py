"""Agent-facing tools for accounts.

Thin wrappers over src.accounts.infra. Read tools run freely. Every write tool is
CONFIRM-GATED via _confirm: it renders a summary table and requires an explicit
yes at the terminal before touching the database.
"""

from anthropic import beta_tool

from app import session
from src.accounts.infra import (
    adjust_account_value,
    create_new_account,
    get_active_account_by_name,
    update_account,
)
from src.accounts.model import AccountType
from src.agent.helpers import _confirm
from src.helpers import cents_to_dollars_str
from src.transactions.model import TransactionType
from src.view_helpers import get_active_accounts, new_table


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
        account = get_active_account_by_name(session, a["account"])
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
        account = get_active_account_by_name(session, u["account"])
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
