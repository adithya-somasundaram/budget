# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# Activate virtualenv first
source env/bin/activate

# Start interactive shell (creates DB on first run, imports all service functions)
python -i scripts.py
```

There is no test suite. Manual testing is done directly in the interactive shell.

## Architecture

This is a Python/Flask + SQLAlchemy CLI budgeting tool. There is no frontend — the user interface is an interactive Python shell (`python -i scripts.py`). Flask is used only to configure the SQLAlchemy app context; there are no HTTP routes beyond a placeholder `/` index.

**Entry points:**
- `scripts.py` — imports everything and pushes the app context + runs `db.create_all()`. This is the only file users run.
- `app.py` — defines the Flask app, SQLAlchemy `db` instance, and `session`. All other modules import `db` and `session` from here.

**Domain modules** live under `src/` and follow a consistent 3-file pattern:
- `model.py` — SQLAlchemy model definition
- `infra.py` — raw DB queries and writes (takes `session` as first arg)
- `services.py` — user-facing functions with `input()` prompts and print output; these are what gets called in the interactive shell

**Domains:** `accounts`, `transactions`, `budget_categories`, `transfers`

**Key conventions:**
- All monetary values are stored and passed as **cents (integers)**, never floats. Use `cents_to_dollars_str()` from `src/helpers.py` for display.
- Account names are stored uppercase (`name.upper()`).
- Soft deletes via `is_active` boolean on `Account` and `BudgetCategory`.
- `Account` and `BudgetCategory` changes are append-logged via SQLAlchemy event listeners into `*Records` tables for history.
- Credit accounts are subtracted when calculating totals (net worth, liquid total, budget leftover).
- `exit_keys = {"quit", "exit"}` in `helpers.py` is used to break out of `while True` input loops in service functions.
