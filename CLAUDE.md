# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# Activate virtualenv first
source env/bin/activate

# Manual input-function shell (creates DB on first run, imports all interactive functions)
python -i shell.py

# Natural-language agent shell (creates DB on first run, drops into the agent)
python -i chat.py
```

There is no test suite. Manual testing is done directly in the interactive shell.

## Architecture

This is a Python/Flask + SQLAlchemy CLI budgeting tool. There is no frontend — the user interface is an interactive Python shell (`python -i shell.py`, or `python -i chat.py` for the agent). Flask is used only to configure the SQLAlchemy app context; there are no HTTP routes beyond a placeholder `/` index.

**Entry points:**
- `bootstrap.py` — shared setup: loads `.env`, pushes the app context, runs `db.create_all()`. Both shells import it first.
- `shell.py` — the manual shell; imports every domain's `commands` (interactive `input()` functions) and prints the function banner.
- `chat.py` — the agent shell; boots and calls `agent()` immediately.
- `app.py` — defines the Flask app, SQLAlchemy `db` instance, and `session`. All other modules import `db` and `session` from here.

**Domain modules** live under `src/` and follow a consistent pattern where `infra.py` is the single shared logic layer that both front-ends call:
- `model.py` — SQLAlchemy model definition
- `infra.py` — raw DB queries/writes **and** business logic (takes `session` as first arg); also holds `*_text` display cores that return strings
- `view.py` — `rich` panel/table rendering
- `commands.py` — human CLI: `input()`-driven functions plus thin `print_*` wrappers over the infra `*_text` cores
- `agent.py` — per-domain `@beta_tool` wrappers that call `infra`; confirm-gated for writes

The agent's conversation loop lives in `src/agent/services.py`, its shared `_confirm` helper in `src/agent/helpers.py`, and `src/agent/tools.py` assembles `ALL_TOOLS` from each domain's `agent.py`.

**Domains:** `accounts`, `transactions`, `budget_categories`, `transfers`

**Key conventions:**
- All monetary values are stored and passed as **cents (integers)**, never floats. Use `cents_to_dollars_str()` from `src/helpers.py` for display.
- Account names are stored uppercase (`name.upper()`).
- Soft deletes via `is_active` boolean on `Account` and `BudgetCategory`.
- `Account` and `BudgetCategory` changes are append-logged via SQLAlchemy event listeners into `*Records` tables for history.
- Credit accounts are subtracted when calculating totals (net worth, liquid total, budget leftover).
- `exit_keys = {"quit", "exit"}` in `helpers.py` is used to break out of `while True` input loops in the `commands.py` functions.
