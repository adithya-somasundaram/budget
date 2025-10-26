from src.budget_categories.model import BudgetCategory


def create_budget_category(session, name: str, amount_in_usd_cents=0):
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
        name=name.upper(), is_active=True, amount_in_usd_cents=amount_in_usd_cents
    )

    try:
        session.add(budget_category)
        session.commit()
        print(
            f"Created budget category with name {name} and value {amount_in_usd_cents} cents"
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

    budget_category.amount_in_usd_cents += adjustment_amount_in_cents
    session.commit()
