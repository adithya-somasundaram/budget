# budget

Welcome to your personal budgeting tool!
Core features:

1. Create accounts that hold money. Think of your debit, investing, retirement, credit accounts
2. Create budgets for categories like food, bills, clothes, etc
3. Record and view transactions that deduct from your accounts (adds to credit accounts) and optionally deducts from your budget

Secondary features:

1. Transfer money between accounts
2. Log credit payments
3. Adjust values in your accounts and budgets

Getting started:

To install all dependencies:

```
pip install requirements.txt
```

To start the application in a terminal shell run:

```
python -i scripts.py
```

This will create the DB if its your first time running, and import all service functions for use. Some of the most useful:

- `bulk_create_accounts`: Will prompt you to input account name, type (debit, credit, venmo, cash, check, investing), and value
- `adjust_account`: Allows you to adjust the value of a given account. Records a transaction to track adjustment.
- `bulk_create_transactions` or `create_transaction_input`: Creates a transaction from an inputted account name. Also takes in transaction type (debit, credit, cash, check, venmo, adjustment). Can optionally deduct from a budget. Default transaction date is current date unless otherwise specified.
- `print_summary`: Displays values of all accounts and sums net worth!
- `create_budget_category` or `adjust_budget_category`: Allows for the creation or adjustment of a budget category
