"""Interactive (human) CLI for budget categories.

`input()`-driven loops plus a thin print wrapper over budget_summary_text in
src.budget_categories.infra. Operations are imported here so they stay available
in the interactive shell via `from src.budget_categories.commands import *`.
"""

from src.helpers import cents_to_dollars_str, exit_keys
from src.budget_categories.infra import (
    budget_summary_text,
    create_budget_category,
    deactivate_budget_category_by_name,
    set_budget_amount,
)
from src.budget_categories.view import make_budget_category_panel


def bulk_create_budget_categories(session) -> None:
    from rich.console import Console

    print(
        "Lets create some budget categories! Enter 'quit' or 'exit' at any time to save and exit."
    )

    console = Console()

    while True:
        console.clear()
        panel, _ = make_budget_category_panel(session)
        console.print(panel)

        name = input("Enter budget category name: ").strip()
        if name.lower() in exit_keys:
            return

        amount = input(
            "Enter budget amount in cents, click 'Enter' to set to 0: "
        ).strip()
        if amount.lower() in exit_keys:
            return
        elif amount == "":
            amount = 0

        try:
            create_budget_category(session, name, int(amount))
        except Exception as e:
            print(f"Error creating budget category: {str(e)}")
            session.rollback()


def deactivate_budget_category(session) -> None:
    """Prompts user to select and deactivate a budget category."""
    from rich.console import Console

    console = Console()
    console.clear()
    panel, mapping = make_budget_category_panel(session)
    console.print(panel)

    selection = input("Enter budget number to deactivate: ").strip()
    if selection.lower() in exit_keys:
        return
    budget_category = mapping.get(int(selection), None)
    if not budget_category:
        print("Invalid budget category selected!")
        return

    deactivate_budget_category_by_name(session, budget_category.name)


def adjust_budget_category(session) -> None:
    """Prompts user to select a budget category and adjust its amount."""
    from rich.console import Console

    console = Console()
    console.clear()
    panel, mapping = make_budget_category_panel(session)
    console.print(panel)

    selection = input("Enter budget number to adjust: ").strip()
    if selection.lower() in exit_keys:
        return
    budget_category = mapping.get(int(selection), None)
    if not budget_category:
        print("Invalid budget category selected!")
        return

    new_amount = input("Enter new budget amount in cents: ").strip()
    if new_amount.lower() in exit_keys:
        return

    set_budget_amount(session, budget_category.name, int(new_amount))
    print(
        f"Adjusted budget category {budget_category.name} to new amount {cents_to_dollars_str(int(new_amount))}"
    )


def print_budget_summary(session) -> None:
    """Prints all active budget categories and remaining liquid assets after budgets."""
    print(budget_summary_text(session))
