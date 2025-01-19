from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///soma.db"
db = SQLAlchemy(app)


@app.route("/")
def index():
    return "Connected"


if __name__ == "__main__":
    app.app_context().push()
    app.run(debug=True, port=9876)
