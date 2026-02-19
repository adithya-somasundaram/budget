from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///budget.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
session = db.session


@app.route("/")
def index():
    return "Connected"


if __name__ == "__main__":
    app.app_context().push()
    app.run(debug=True, port=9876)
