from src.transactions.model import TransactionType


class AccountNameType:
    def __init__(self, name: str, transaction_type: TransactionType):
        self.name = name
        self.transaction_type = transaction_type
