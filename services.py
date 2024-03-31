from app import db
from models import Transaction, TransactionType
from sqlalchemy.sql import func

session = db.session

def create_new_transaction(amount_in_cents:int, type:TransactionType, description:str):
    new_transaction = Transaction(amount_in_cents=amount_in_cents, type=type, description=description)
    try:
        session.add(new_transaction)
        session.commit()
        print('Successfully create transaction of type ' + str(type) + ' and amount ' + str(amount_in_cents) + '\n' + description)
    except:
        print('Could not create transaction of type ' + str(type) + ' and amount ' + str(amount_in_cents))

def print_cents_in_dollars(amount):
    dollars = int(amount / 100)
    cents = amount % 100

    if cents < 10:
        cents = '0' + str(cents)
    else:
        cents = str(cents)

    return '$' + str(dollars) + '.' + cents

def get_summary():
    totals = session.query(Transaction.type, func.sum(Transaction.amount_in_cents).label('amount_in_cents')).group_by(Transaction.type).all()

    for total in totals:
        print(str(total.type) + ': ' + print_cents_in_dollars(total.amount_in_cents))