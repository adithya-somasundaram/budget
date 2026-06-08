from app import *
from src.accounts.services import *
from src.budget_categories.services import *
from src.transfers.services import *
from src.transactions.services import *

app.app_context().push()
db.create_all()

print(
    """
Available functions:
- bulk_create_accounts: create accounts
- bulk_adjust_accounts: adjust account values (e.g. investment accounts)
- bulk_create_budget_categories: create budget categories
- adjust_budget_category: adjust a budget category's amount
- deactivate_budget_category: deactivate a budget category
- bulk_create_transactions: create transactions
- transfer_input: transfer between accounts
- create_credit_payment: pay off a credit account
- print_summary / print_liquid_summary: view account and budget summaries
- view_all_transactions: view recorded transactions
"""
)
