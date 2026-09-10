import os


def _load_dotenv(path=".env"):
    """Loads KEY=VALUE lines from a .env file into the environment if present.

    No dependency; only sets vars that aren't already set, so a real exported
    env var still wins. Used to pick up ANTHROPIC_API_KEY for the agent.
    """
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

from app import *
from src.accounts.commands import *
from src.budget_categories.commands import *
from src.transfers.commands import *
from src.transactions.commands import *
from src.agent.services import agent

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
- agent: open a conversational assistant to enter transactions/budgets/adjustments in plain language
"""
)
