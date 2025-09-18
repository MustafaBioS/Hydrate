from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, logout_user, current_user

# Initialization

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SECRET_KEY'] = 'Hydrate'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# DB Models

class Users(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)


# Routes

@app.route('/')
def home():
    return render_template('index.html')


# Run

if __name__ == '__main__':
    app.run(debug=True)