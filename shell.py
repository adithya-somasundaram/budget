"""Manual budgeting shell.

Run with:  python -i shell.py

Boots the app (creates the DB on first run) and imports all the interactive
input functions so you can call them at the Python prompt. For the natural-language
agent instead, use `python -i chat.py`.
"""

from bootstrap import app, db, session
from src.accounts.commands import *
from src.budget_categories.commands import *
from src.transfers.commands import *
from src.transactions.commands import *

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

For the natural-language agent, run: python -i chat.py
"""
)
