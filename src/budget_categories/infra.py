from src.budget_categories.model import BudgetCategory


def get_budget_category_mapping(session) -> dict[int, BudgetCategory]:
    """Returns mapping of integer to budget category object for all active budget categories. Good for user input."""
    active_budget_categories = _get_all_active_budget_categories(session)
    return {
        i: budget_category
        for i, budget_category in enumerate(active_budget_categories, 1)
    }


def _get_all_active_budget_categories(session) -> list[BudgetCategory]:
    """Returns list of all active budget category names"""
    return (
        session.query(BudgetCategory)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )
