from src.accounts.infra import get_liquid_total
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str


def get_budget_leftover(session) -> int:
    """Returns unbudgeted liquid cash in cents: liquid total minus money still
    earmarked in budgets. This equals liquid total minus the sum of budgets while
    budgets are healthy; an overspent (negative) category counts as 0 earmarked so
    it does not inflate the leftover (the overage already left the accounts and is
    reflected in the liquid total)."""
    earmarked = sum(
        max(0, category.amount_in_cents)
        for category in _get_all_active_budget_categories(session)
    )
    return get_liquid_total(session) - earmarked


def create_budget_category(session, name: str, amount_in_cents=0) -> None:
    """Creates new budget category with given name and amount_in_cents. Name must be unique among active budget categories."""
    # check for dupes
    dupe_check = (
        session.query(BudgetCategory)
        .filter(BudgetCategory.name == name.upper(), BudgetCategory.is_active == True)
        .first()
    )

    if dupe_check:
        raise Exception(
            f"Budget with name {name} exists with value {dupe_check.amount_in_cents}"
        )

    budget_category = BudgetCategory(
        name=name.upper(), is_active=True, amount_in_cents=amount_in_cents
    )

    session.add(budget_category)
    session.commit()
    print(f"Created budget category with name {name} and value {amount_in_cents} cents")


def get_active_budget_category_by_name(session, name: str) -> BudgetCategory:
    """Returns the active budget category with this name (case-insensitive), or None.

    Shared lookup used by the human CLI and the agent tools.
    """
    return (
        session.query(BudgetCategory)
        .filter(BudgetCategory.name == name.upper(), BudgetCategory.is_active == True)
        .first()
    )


def set_budget_amount(session, name: str, new_amount_cents: int) -> BudgetCategory:
    """Sets an active budget category to a new absolute amount, creating it if it
    does not exist. Single home for the "set a budget's value" operation shared by
    the interactive CLI and the agent's set_budgets tool.
    """
    category = get_active_budget_category_by_name(session, name)
    if category:
        category.amount_in_cents = new_amount_cents
        session.commit()
    else:
        create_budget_category(session, name, new_amount_cents)
    return category


def deactivate_budget_category_by_name(session, name: str) -> None:
    """Soft-deletes the active budget category with this name."""
    category = get_active_budget_category_by_name(session, name)
    if not category:
        raise Exception(f"No active budget category found with name {name}!")
    category.is_active = False
    session.commit()
    print(f"Deactivated budget category {category.name}")


def get_budget_category_mapping(session) -> dict[int, BudgetCategory]:
    """Returns mapping of integer to budget category object for all active budget categories. Good for user input."""
    active_budget_categories = _get_all_active_budget_categories(session)
    return {
        i: budget_category
        for i, budget_category in enumerate(active_budget_categories, 1)
    }


def budget_summary_text(session) -> str:
    """Builds the budget summary string (active categories + LEFTOVER).

    Returns the text so both the human CLI (which prints it) and the account
    summary / agent (which embed it) share the same compute+format logic.
    """
    categories = (
        session.query(BudgetCategory.name, BudgetCategory.amount_in_cents)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )

    if len(categories) == 0:
        return "No active budget categories."

    output = ""

    max_name_len = max(len(c.name) for c in categories)
    label_len = max(max_name_len, len("LEFTOVER"))

    for category in categories:
        output += f"{category.name:<{label_len}} : {cents_to_dollars_str(category.amount_in_cents)}\n"

    leftover = get_budget_leftover(session)

    output += f"{'LEFTOVER':<{label_len}} : {cents_to_dollars_str(leftover)}"
    return output


def _get_all_active_budget_categories(session) -> list[BudgetCategory]:
    """Returns list of all active budget category objects"""
    return (
        session.query(BudgetCategory)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )
