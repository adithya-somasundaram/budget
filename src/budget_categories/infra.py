from src.budget_categories.model import BudgetCategory


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
