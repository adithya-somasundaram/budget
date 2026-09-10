"""Shared agent helpers.

Cross-domain bits used by every per-domain agent.py. Imports nothing from the
domain modules, so it can be imported by them without a cycle.
"""

from rich.console import Console

console = Console()


def _confirm(table, prompt="Apply these changes?") -> bool:
    """Prints a summary table and blocks for an explicit yes/no at the terminal."""
    console.print(table)
    answer = input(f"{prompt} (yes/no): ").strip().lower()
    return answer in ("y", "yes")
