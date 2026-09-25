"""Agent-facing tools for budget categories.

Thin wrappers over src.budget_categories.infra. list_budget_categories reads
freely; set_budgets is CONFIRM-GATED via _confirm.
"""

from anthropic import beta_tool

from app import session
from src.agent.helpers import _confirm
from src.budget_categories.infra import (
    get_active_budget_category_by_name,
    get_budget_leftover,
    set_budget_amount,
)
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str
from src.view_helpers import new_table


@beta_tool
def list_budget_categories() -> str:
    """List all active budget categories with their remaining amount, plus the
    current LEFTOVER (unbudgeted liquid cash). Use this to resolve a budget name
    the user mentions and to see current remaining amounts.
    """
    categories = (
        session.query(BudgetCategory)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )
    lines = [
        f"{c.name} | remaining={cents_to_dollars_str(c.amount_in_cents)}"
        for c in categories
    ]
    lines.append(f"LEFTOVER | {cents_to_dollars_str(get_budget_leftover(session))}")
    return "\n".join(lines)


@beta_tool
def set_budgets(budgets: list[dict]) -> str:
    """Create budget categories or set existing ones to a new absolute amount, after
    showing a before/after table and getting confirmation.

    Each item in `budgets` is an object with:
      - name (str, required): the budget category name.
      - new_amount_cents (int, required): the new absolute remaining amount in cents.

    A name that does not exist yet is created; an existing one is set to the new
    amount. Returns a message stating whether the user confirmed.
    """
    staged = []
    for b in budgets:
        existing = get_active_budget_category_by_name(session, b["name"])
        staged.append(
            {
                "name": b["name"].upper(),
                "existing": existing,
                "old": existing.amount_in_cents if existing else None,
                "new": int(b["new_amount_cents"]),
            }
        )

    table = new_table("Budget", "Before", "After", justify_first_right=False)
    for s in staged:
        table.add_row(
            s["name"],
            cents_to_dollars_str(s["old"]) if s["existing"] else "(new)",
            cents_to_dollars_str(s["new"]),
        )

    if not _confirm(table, "Apply these budget changes?"):
        return "User declined. Nothing was written. Ask what they'd like to change."

    for s in staged:
        set_budget_amount(session, s["name"], s["new"])
    return f"Confirmed. Set {len(staged)} budget(s)."
