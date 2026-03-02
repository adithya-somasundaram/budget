from src.budget_categories.model import BudgetCategory


def create_budget_category(session, name: str, amount_in_cents=0):
    # check for dupes
    dupe_check = (
        session.query(BudgetCategory)
        .filter(BudgetCategory.name == name.upper(), BudgetCategory.is_active == True)
        .first()
    )

    if dupe_check:
        print(f"Budget with name {name} exists with value {dupe_check.amount_in_cents}")
        return

    budget_category = BudgetCategory(
        name=name.upper(), is_active=True, amount_in_cents=amount_in_cents
    )

    try:
        session.add(budget_category)
        session.commit()
        print(
            f"Created budget category with name {name} and value {amount_in_cents} cents"
        )
    except Exception as e:
        print(f"Error creating budget category: {str(e)}")


def deactivate_budget_category(session, budget_category_name: str):
    budget_category = (
        session.query(BudgetCategory)
        .filter(
            BudgetCategory.name == budget_category_name.upper(),
            BudgetCategory.is_active == True,
        )
        .first()
    )

    if not budget_category:
        print(f"Could not find budget category with name {budget_category_name}")
        return

    budget_category.is_active = False
    session.commit()


def adjust_budget_category(
    session, budget_category_name: str, adjustment_amount_in_cents: int
):
    budget_category = (
        session.query(BudgetCategory)
        .filter(
            BudgetCategory.name == budget_category_name.upper(),
            BudgetCategory.is_active == True,
        )
        .first()
    )

    if not budget_category:
        print(f"Could not find budget category with name {budget_category_name}")
        return

    budget_category.amount_in_cents += adjustment_amount_in_cents
    session.commit()


def get_all_active_budget_categories(session):
    """Returns list of all active budget category names"""
    return (
        session.query(BudgetCategory.id, BudgetCategory.name)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )


def get_budget_category_mapping(session):
    """Returns mapping of budget category name to budget category object for all active budget categories"""
    active_budget_categories = get_all_active_budget_categories(session)
    result = {}
    for i in range(len(active_budget_categories)):
        result[i] = active_budget_categories[i].name
    return result
