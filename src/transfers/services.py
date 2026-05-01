from src.accounts.infra import get_all_accounts_mapping
from src.helpers import exit_keys
from src.transfers.infra import transfer


def transfer_input(session):
    """Transfers amount from one account to another."""
    amount_in_cents = input("Enter transfer amount in cents: ").strip()
    if amount_in_cents.lower() in exit_keys:
        return
    amount_in_cents = int(amount_in_cents)

    account_mapping = get_all_accounts_mapping(session)

    # User selects from account from list of active accounts
    print("Enter from account number: ")
    for i, account in account_mapping.items():
        print(f"({i}) {account.name}")
    from_account_id = input().strip()
    if from_account_id.lower() in exit_keys:
        return
    from_account = account_mapping.get(int(from_account_id), None)
    if not from_account:
        raise Exception("Invalid account selected!")

    # User selects to account from list of active accounts
    print("Enter to account number: ")
    for i, account in account_mapping.items():
        print(f"({i}) {account.name}")
    to_account_id = input().strip()
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
            from_account.transaction_type == "CREDIT",
            description if description != "" else None,
        )
    except Exception as e:
        print(f"Transfer failed: {str(e)}")
        return

    print(
        f"Successfully transferred {amount_in_cents} from {from_account.name} to {to_account.name}!"
    )


def create_credit_payment(session):
    """Subtracts amount from credit account and another paying account."""
    amount_in_cents = input("Enter transfer amount in cents: ").strip()
    if amount_in_cents.lower() in exit_keys:
        return
    amount_in_cents = int(amount_in_cents)

    credit_account_mapping = get_all_accounts_mapping(session, "CREDIT")
    account_mapping = get_all_accounts_mapping(session)

    # User selects from account from list of active accounts
    print("Enter credit account: ")
    for i, account in credit_account_mapping.items():
        print(f"({i}) {account.name}")
    from_account_id = input().strip()
    if from_account_id.lower() in exit_keys:
        return
    from_account = credit_account_mapping.get(int(from_account_id), None)
    if not from_account:
        raise Exception("Invalid account selected!")

    # User selects to account from list of active accounts
    print("Enter to paying account number: ")
    for i, account in account_mapping.items():
        print(f"({i}) {account.name}")
    to_account_id = input().strip()
    if to_account_id.lower() in exit_keys:
        return
    to_account = account_mapping.get(int(to_account_id), None)
    if not to_account:
        raise Exception("Invalid account selected!")

    try:
        transfer(
            session,
            from_account.id,
            to_account.id,
            amount_in_cents,
            True,
            f"Credit payment from {from_account.name} to {to_account.name}",
        )
    except Exception as e:
        print(f"Credit payment failed: {str(e)}")
        return

    print(
        f"Successfully paid {amount_in_cents} from {from_account.name} to {to_account.name}!"
    )
