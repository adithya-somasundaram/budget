from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import enum
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soma.db'
db = SQLAlchemy(app)

class TransactionType(enum.Enum):
    CREDIT = 1
    DEBIT = 2
    CASH = 3
    CHECK = 4

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    amount_in_cents = db.Column(db.Integer, nullable=False)
    type = db.Column(Enum(TransactionType), nullable=False)
    description = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

def create_new_transaction(amount_in_cents:int, type:TransactionType):
    new_transaction = Transaction(amount_in_cents=amount_in_cents, type=type)
    try:
        db.session.add(new_transaction)
        db.session.commit()
    except:
        print('Could not create transaction of type ' + type + ' and amount ' + str(amount_in_cents))


@app.route('/')
def index():
    return 'Connected'

if __name__ == '__main__':
    app.app_context().push()
    app.run(debug=True, port=9876)