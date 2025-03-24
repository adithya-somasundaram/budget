from src.accounts.model import AccountType
from src.accounts.services import create_new_account


def create_accounts(session):
    create_new_account(session, "Keypoint", AccountType.DEBIT)
    create_new_account(session, "Keypoint_Credit", AccountType.CREDIT)

    create_new_account(session, "Fidelity_Investing", AccountType.INVESTING)
    create_new_account(session, "Fidelity_Credit", AccountType.CREDIT)
    create_new_account(session, "Fidelity_Roth", AccountType.INVESTING)
    create_new_account(session, "Fidelity_401k", AccountType.INVESTING)

    create_new_account(session, "Cash", AccountType.CASH)
    create_new_account(session, "Check", AccountType.CHECK)
    create_new_account(session, "Venmo", AccountType.VENMO)

    print("DONE")
