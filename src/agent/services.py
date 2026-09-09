"""Conversational agent entry point.

`agent()` opens an open-ended conversation: describe your transactions, budget
changes, or account adjustments in plain language and the agent proposes them as
a table you confirm before anything is written. Type 'quit' or 'exit' to leave.
"""

import anthropic

from src.agent.tools import ALL_TOOLS
from src.helpers import exit_keys

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are a budgeting assistant embedded in a personal-finance CLI.
The user will describe transactions, budget changes, and account adjustments in
plain language, often several at once. Your job is to turn those into precise
tool calls.

Conventions you MUST follow:
- All money is in integer CENTS. $42.50 is 4250. Never use floats or dollars in tool inputs.
- Account and budget names are stored UPPERCASE. Match them case-insensitively.
- Spending money is direction "decrement" (the default). Income (paychecks, refunds,
  deposits) is direction "increment".
- Credit-account math is handled for you: a "decrement" on a credit account increases
  what is owed. Do NOT try to invert amounts yourself for credit accounts.
- Before recording anything, call list_accounts and/or list_budget_categories to
  resolve the exact names the user means and to learn account types. If a name is
  ambiguous or missing, ask the user rather than guessing.
- A credit-card payment is NOT a transaction. Use pay_credit for it: it lowers both the
  paying account and what is owed on the card. Never record a credit payment with
  record_transactions (that touches only one account and leaves the card unpaid).
- The write tools (record_transactions, create_accounts, adjust_accounts, update_accounts, pay_credit, set_budgets) show the user a
  summary and ask for confirmation themselves. Do not ask for confirmation in text
  first; just call the tool with your best proposal. If a tool reports the user
  declined, ask what they want to change and try again.
- Batch related items into a single tool call (e.g. all transactions at once) so the
  user sees one summary table.

Be concise. After a tool reports success, briefly confirm what was done."""


def agent() -> None:
    """Starts an interactive budgeting conversation. Type 'quit' or 'exit' to leave."""
    client = anthropic.Anthropic()
    messages = []

    print(f"Budget agent ready ({MODEL}). Describe your transactions or changes. Type 'quit' to exit.\n")

    while True:
        user_input = input("you> ").strip()
        if user_input.lower() in exit_keys:
            print("Bye!")
            return
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        runner = client.beta.messages.tool_runner(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            messages=messages,
        )

        last = None
        for message in runner:
            last = message
            # Mirror history so the conversation carries across turns.
            messages.append({"role": "assistant", "content": message.content})
            tool_response = runner.generate_tool_call_response()
            if tool_response is not None:
                messages.append(tool_response)

            for block in message.content:
                if block.type == "text" and block.text.strip():
                    print(f"\nagent> {block.text.strip()}\n")
