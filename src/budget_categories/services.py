from src.accounts.services import get_liquid_total
from src.budget_categories.model import BudgetCategory
from src.helpers import cents_to_dollars_str


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


def print_budget_summary(session):
    """Prints all active budget categories and remaining liquid assets after budgets."""
    categories = (
        session.query(BudgetCategory.name, BudgetCategory.amount_in_cents)
        .filter(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.name.asc())
        .all()
    )

    output = ""
    budget_total = 0

    max_name_len = max(len(c.name) for c in categories)
    label_len = max(max_name_len, len("LEFTOVER"))

    for category in categories:
        budget_total += category.amount_in_cents
        output += f"{category.name:<{label_len}} : {cents_to_dollars_str(category.amount_in_cents)}\n"

    liquid_total = get_liquid_total(session)
    leftover = liquid_total - budget_total

    output += f"{'TOTAL':<{label_len}} : {cents_to_dollars_str(budget_total)}\n"
    output += f"{'LEFTOVER':<{label_len}} : {cents_to_dollars_str(leftover)}"
    print(output)


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
