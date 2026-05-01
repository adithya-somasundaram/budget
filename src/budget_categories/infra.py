from src.budget_categories.model import BudgetCategory


def _get_all_active_budget_categories(session):
    """Returns list of all active budget category names"""
    return (
        session.query(BudgetCategory.id, BudgetCategory.name)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )


def get_budget_category_mapping(session):
    """Returns mapping of budget category name to budget category object for all active budget categories"""
    active_budget_categories = _get_all_active_budget_categories(session)
    result = {}
    for i in range(len(active_budget_categories)):
        result[i] = active_budget_categories[i].name
    return result
