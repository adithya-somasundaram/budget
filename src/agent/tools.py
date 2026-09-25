"""Agent tool registry.

The tool implementations live in each domain's agent.py (co-located with that
domain's infra). This module just imports them and assembles ALL_TOOLS in a
stable order — the order and names are what the model and system prompt reference,
so keep them fixed.

Every write tool is CONFIRM-GATED (see src.agent.helpers._confirm): it renders a
summary table and requires an explicit yes at the terminal before it touches the
database, so a write can never happen without the user seeing exactly what is
about to change.
"""

from src.accounts.agent import (
    adjust_accounts,
    create_accounts,
    list_accounts,
    update_accounts,
)
from src.budget_categories.agent import list_budget_categories, set_budgets
from src.transactions.agent import record_transactions
from src.transfers.agent import pay_credit, transfer_funds

ALL_TOOLS = [
    list_accounts,
    list_budget_categories,
    record_transactions,
    create_accounts,
    adjust_accounts,
    update_accounts,
    transfer_funds,
    pay_credit,
    set_budgets,
]
