"""Agent-facing tools for transfers.

transfer_funds and pay_credit are CONFIRM-GATED via _confirm. Their balance /
credit-vs-non-credit validation is front-end-shaped (it returns guidance strings
for the model), so it lives here rather than in infra; the core write is the
shared src.transfers.infra.transfer.
"""

from anthropic import beta_tool

from app import session
from src.accounts.infra import get_active_account_by_name
from src.accounts.model import AccountType
from src.agent.helpers import _confirm
from src.helpers import cents_to_dollars_str
from src.transfers.infra import transfer
from src.view_helpers import new_table


@beta_tool
def transfer_funds(transfers: list[dict]) -> str:
    """Move money between two of your own accounts (e.g. checking -> investing, or
    checking -> savings), after showing a before/after table and getting confirmation.

    A transfer is NOT a transaction and NOT income or spending: money leaves one of
    your accounts and lands in another, so your net worth is unchanged. It lowers the
    source account and raises the destination account, and is logged in the transfer
    ledger. Use this whenever the user says they moved / transferred money between
    their own accounts. Do NOT use record_transactions for this (that would only touch
    one account and mislabel it as spending or income).

    For paying off a credit card, use pay_credit instead, not this tool.

    Each item in `transfers` is an object with:
      - from_account (str, required): the account the money comes from (non-credit).
      - to_account (str, required): the account the money goes to.
      - amount_cents (int, required): the amount in cents. Must not exceed the source
        account's balance.

    Call list_accounts first to resolve names. Returns a message stating whether the
    user confirmed.
    """
    staged = []
    for tr in transfers:
        src = get_active_account_by_name(session, tr["from_account"])
        if not src:
            return f"No active account named '{tr['from_account']}'. Nothing was written; ask the user to clarify."
        if src.type == AccountType.CREDIT:
            return f"'{src.name}' is a credit account — to pay it down use pay_credit, not a transfer. Nothing was written."

        dst = get_active_account_by_name(session, tr["to_account"])
        if not dst:
            return f"No active account named '{tr['to_account']}'. Nothing was written; ask the user to clarify."

        amount = int(tr["amount_cents"])
        if amount > src.value_in_cents:
            return f"Transfer of {cents_to_dollars_str(amount)} exceeds {src.name}'s balance of {cents_to_dollars_str(src.value_in_cents)}. Nothing was written; ask the user to confirm the amount."

        staged.append({"src": src, "dst": dst, "amount": amount})

    table = new_table("Amount", "From", "To", justify_first_right=False)
    for s in staged:
        src_after = s["src"].value_in_cents - s["amount"]
        dst_after = s["dst"].value_in_cents + s["amount"]
        table.add_row(
            cents_to_dollars_str(s["amount"]),
            f"{s['src'].name}: {cents_to_dollars_str(s['src'].value_in_cents)} -> {cents_to_dollars_str(src_after)}",
            f"{s['dst'].name}: {cents_to_dollars_str(s['dst'].value_in_cents)} -> {cents_to_dollars_str(dst_after)}",
        )

    if not _confirm(table, "Make these transfers?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        try:
            transfer(
                session,
                s["src"].id,
                s["dst"].id,
                s["amount"],
                f"Transfer from {s['src'].name} to {s['dst'].name}",
            )
        except Exception as e:
            session.rollback()
            return f"Transfer failed: {e}. Some transfers may not have been applied; ask the user how to proceed."
    return f"Confirmed. Made {len(staged)} transfer(s)."


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
        credit = get_active_account_by_name(session, p["credit_account"])
        if not credit:
            return f"No active account named '{p['credit_account']}'. Nothing was written; ask the user to clarify."
        if credit.type != AccountType.CREDIT:
            return f"'{credit.name}' is not a credit account, so it can't be paid off this way. Nothing was written; ask the user to clarify."

        paying = get_active_account_by_name(session, p["paying_account"])
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
