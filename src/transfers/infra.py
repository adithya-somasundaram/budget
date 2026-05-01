from datetime import datetime

from src.accounts.model import Account
from src.helpers import pacific_timezone
from src.transfers.model import TransferLedger


def transfer(
    session,
    from_account_id: int,
    to_account_id: int,
    amount_in_cents: int,
    is_credit_payment: bool,
    description: str = None,
) -> None:
    """Helper function to transfer amount from one account to another. Both accounts must be active."""
    # Fetch from account
    from_account_obj: Account = (
        session.query(Account)
        .filter(Account.id == from_account_id, Account.is_active == True)
        .first()
    )

    # Validate from account and amount exceeds transfer amount
    if not from_account_obj:
        raise Exception(f"No active account FROM account found!")
    if amount_in_cents > from_account_obj.value_in_cents:
        raise Exception(
            f"{amount_in_cents} greater than accounts value {from_account_obj.value_in_cents}!"
        )

    before_from_account_balance = from_account_obj.value_in_cents

    # Fetch to account
    to_account_obj: Account = (
        session.query(Account)
        .filter(Account.id == to_account_id, Account.is_active == True)
        .first()
    )

    # Validate to account
    if not to_account_obj:
        raise Exception(f"No active account TO account found!")

    before_to_account_balance = to_account_obj.value_in_cents

    # Perform transfer
    if is_credit_payment:
        to_account_obj.value_in_cents -= amount_in_cents
    else:
        to_account_obj.value_in_cents += amount_in_cents
    from_account_obj.value_in_cents -= amount_in_cents

    ledger = TransferLedger(
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount_in_cents=amount_in_cents,
        from_account_after_balance_in_cents=from_account_obj.value_in_cents,
        to_account_after_balance_in_cents=to_account_obj.value_in_cents,
        from_account_before_balance_in_cents=before_from_account_balance,
        to_account_before_balance_in_cents=before_to_account_balance,
        is_credit_payment=is_credit_payment,
        description=description,
        date_of_transaction=datetime.now(pacific_timezone).date(),
    )
    session.add(ledger)
    session.commit()
