"""Budget agent shell.

Run with:  python -i chat.py

Boots the app (creates the DB on first run) and drops you straight into the
conversational agent. Type 'quit' or 'exit' to leave the agent; you are returned
to your normal command line (the script exits even under `python -i`, so there is
no lingering Python prompt). For the manual input-function shell instead, use
`python -i shell.py`.
"""

import os
import sys

from bootstrap import app, db, session
from src.agent.services import agent

agent()

# The agent loop has exited (user typed quit/exit). Return straight to the shell
# instead of dropping into the Python interactive prompt that `python -i` would
# otherwise leave open. Flush first so any buffered output is written, then exit
# hard — os._exit skips the -i inspect step that sys.exit() would still trigger.
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
