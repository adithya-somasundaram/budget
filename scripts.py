from app import *
from src.accounts.services import (
    adjust_account_value,
    bulk_create_accounts,
    create_new_account,
    deactivate_account,
    print_liquid_summary,
    print_summary,
)
from src.budget_categories.services import (
    adjust_budget_category,
    create_budget_category,
    deactivate_budget_category,
    print_budget_summary,
)
from src.transfers.services import create_credit_payment, transfer_input
from src.transactions.services import bulk_create_transactions, create_transaction_input

app.app_context().push()
db.create_all()
