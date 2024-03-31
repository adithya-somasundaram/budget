from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import enum
from datetime import datetime
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soma.db'
db = SQLAlchemy(app)

class TransactionType(enum.Enum):
    CREDIT = 1
    DEBIT = 2
    CASH = 3
    CHECK = 4
    VENMO = 5

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    amount_in_cents = db.Column(db.Integer, nullable=False)
    type = db.Column(Enum(TransactionType), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

def create_new_transaction(amount_in_cents:int, type:TransactionType, description:str):
    new_transaction = Transaction(amount_in_cents=amount_in_cents, type=type, description=description)
    try:
        db.session.add(new_transaction)
        db.session.commit()
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
    totals = db.session.query(Transaction.type, func.sum(Transaction.amount_in_cents).label('amount_in_cents')).group_by(Transaction.type).all()

    for total in totals:
        print(str(total.type) + ': ' + print_cents_in_dollars(total.amount_in_cents))

@app.route('/')
def index():
    return 'Connected'

if __name__ == '__main__':
    app.app_context().push()
    app.run(debug=True, port=9876)