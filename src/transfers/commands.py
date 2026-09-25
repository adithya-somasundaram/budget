from src.accounts.infra import get_all_accounts_mapping
from src.accounts.model import AccountType
from src.helpers import exit_keys
from src.transfers.infra import transfer


def transfer_input(session) -> None:
    """Transfers amount from one account to another."""
    from rich.console import Console
    from src.accounts.view import make_accounts_panel

    console = Console()
    console.clear()
    console.print(make_accounts_panel(session))

    amount_in_cents = input("Enter transfer amount in cents: ").strip()
    if amount_in_cents.lower() in exit_keys:
        return
    amount_in_cents = int(amount_in_cents)

    account_mapping = get_all_accounts_mapping(session)

    from_account_id = input("Enter from account number: ").strip()
    if from_account_id.lower() in exit_keys:
        return
    from_account = account_mapping.get(int(from_account_id), None)
    if not from_account:
        raise Exception("Invalid account selected!")

    to_account_id = input("Enter to account number: ").strip()
    if to_account_id.lower() in exit_keys:
        return
    to_account = account_mapping.get(int(to_account_id), None)
    if not to_account:
        raise Exception("Invalid account selected!")

    description = input(
        "Enter description for transfer, click 'Enter' to skip: "
    ).strip()

    try:
        transfer(
            session,
            from_account.id,
            to_account.id,
            amount_in_cents,
            description if description != "" else None,
        )
    except Exception as e:
        print(f"Transfer failed: {str(e)}")
        return

    print(
        f"Successfully transferred {amount_in_cents} from {from_account.name} to {to_account.name}!"
    )


def create_credit_payment(session) -> None:
    """Subtracts amount from credit account and another paying account."""
    from rich.console import Console
    from src.accounts.view import make_credit_payment_panel

    console = Console()
    console.clear()
    console.print(make_credit_payment_panel(session))

    amount_in_cents = input("Enter transfer amount in cents: ").strip()
    if amount_in_cents.lower() in exit_keys:
        return
    amount_in_cents = int(amount_in_cents)

    credit_account_mapping = get_all_accounts_mapping(session, AccountType.CREDIT)
    paying_account_mapping = {
        i: account
        for i, account in enumerate(
            (a for a in get_all_accounts_mapping(session).values() if a.type != AccountType.CREDIT),
            1,
        )
    }

    from_account_id = input("Enter credit account number: ").strip()
    if from_account_id.lower() in exit_keys:
        return
    from_account = credit_account_mapping.get(int(from_account_id), None)
    if not from_account:
        raise Exception("Invalid account selected!")

    to_account_id = input("Enter paying account number: ").strip()
    if to_account_id.lower() in exit_keys:
        return
    to_account = paying_account_mapping.get(int(to_account_id), None)
    if not to_account:
        raise Exception("Invalid account selected!")

    try:
        transfer(
            session,
            from_account.id,
            to_account.id,
            amount_in_cents,
            f"Credit payment from {from_account.name} to {to_account.name}",
        )
    except Exception as e:
        print(f"Credit payment failed: {str(e)}")
        return

    print(
        f"Successfully paid {amount_in_cents} from {from_account.name} to {to_account.name}!"
    )
