# budget

Welcome to your personal budgeting tool!
Core features:

1. Create accounts that hold money. Think of your debit, investing, retirement, credit accounts
2. Create budgets for categories like food, bills, clothes, etc
3. Record and view transactions that increment or decrement your accounts (credit accounts work in reverse — a decrement increases what you owe) and optionally adjust your budget

Secondary features:

1. Transfer money between accounts
2. Log credit payments
3. Adjust values in your accounts and budgets

Getting started:

To install all dependencies:

```
pip install -r requirements.txt
```

To start the application in a terminal shell run:

```
python -i scripts.py
```

This will create the DB if its your first time running, and import all service functions for use. Some of the most useful:

- `bulk_create_accounts`: Will prompt you to input account name, type (debit, credit, venmo, cash, check, investing), and value
- `adjust_account_value`: Allows you to adjust the value of a given account. Records a transaction to track adjustment.
- `transfer_input`: Transfers value from one account to another. Recorded in the transfer ledger, not as a transaction.
- `bulk_create_transactions`: Creates transactions from an inputted account name. Also takes in transaction type (debit, credit, cash, check, venmo, adjustment). Can optionally deduct from a budget. Default transaction date is current date unless otherwise specified.
- `print_summary`: Displays values of all accounts, budgets and sums net worth!
- `bulk_create_budget_categories`, `adjust_budget_category` or `deactivate_budget_category`: Allows for the creation or adjustment of a budget category
- `create_credit_payment`: Handles paying off a credit account at the deduction of another account. Recorded in the transfer ledger, not as a transaction.
