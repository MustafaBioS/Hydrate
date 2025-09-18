from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, login_user, logout_user, current_user, LoginManager
from sqlalchemy.exc import IntegrityError

# Initialization

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SECRET_KEY'] = 'Hydrate'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# DB Models

class Users(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    pfp = db.Column(db.String(200), default='/static/uploads/default.png')


# Routes

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

            newuser = Users(username=username, password=hashed_pw)

            db.session.add(newuser)
            db.session.commit()
            flash('Account Created Successfully', 'success')
            login_user(newuser)
            
            return redirect(url_for('home'))

        except IntegrityError:
            db.session.rollback()
            flash('Username Already Taken', 'fail')
            return redirect(url_for('signup'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Successfully Logged In', 'success')
            return redirect(url_for('home'))
        else: 
            flash('Incorrect Credentials', 'fail')
            return redirect(url_for('login'))

# Run

if __name__ == '__main__':
    app.run(debug=True)