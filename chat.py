"""Budget agent shell.

Run with:  python -i chat.py

Boots the app (creates the DB on first run) and drops you straight into the
conversational agent. Type 'quit' or 'exit' to leave the agent; because this is
run with `python -i`, you land at the Python prompt afterwards (with `session`
available) and can call `agent()` again or poke around. For the manual
input-function shell instead, use `python -i shell.py`.
"""

from bootstrap import app, db, session
from src.agent.services import agent

agent()
