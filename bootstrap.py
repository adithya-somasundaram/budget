"""Shared setup for the interactive entry points (shell.py, chat.py).

Loads .env, pushes the Flask app context, and creates tables. Import this first
from an entry point, then import whatever functions that shell should expose.
"""

import os


def _load_dotenv(path=".env"):
    """Loads KEY=VALUE lines from a .env file into the environment if present.

    No dependency; only sets vars that aren't already set, so a real exported
    env var still wins. Used to pick up ANTHROPIC_API_KEY for the agent.
    """
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

from app import app, db, session

app.app_context().push()
db.create_all()
