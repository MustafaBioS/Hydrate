from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, login_user, logout_user, current_user, LoginManager, login_required
from sqlalchemy.exc import IntegrityError
import os
from PIL import Image


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
    watergoal = db.Column(db.Integer, default=3000)

# Routes

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
@login_required
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully Logged Out', 'success')
    return redirect(url_for('login'))

@app.route('/user/<int:user_id>', methods = ['GET', 'POST'])
@login_required
def user(user_id):

    if user_id != current_user.id:
        flash('Unauthorized Access', 'fail')
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template('user.html', user_id=current_user.id)
    if request.method == 'POST':
        user = Users.query.filter_by(username=current_user.username).first()

        newuser = request.form.get('newuser')
        verify = request.form.get('verify')

        newpfp = request.files.get('newpfp')

        newgoal = request.form.get('newgoal')

        oldpass = request.form.get('oldpass')
        newpass = request.form.get('newpass')

        deletepass = request.form.get('deletepass')
        confirmpass = request.form.get('confirmpass')

        if newuser and verify:
            if bcrypt.check_password_hash(user.password, verify):
                    
                if Users.query.filter_by(username=newuser).first():
                    flash("That username is already taken.", "danger")
                    return redirect(url_for('user', user_id=user_id))
                else:
                    user.username = newuser
                    db.session.commit()
                    flash("Username Updated Successfully", 'success')
                    return redirect(url_for('user', user_id=user_id))
            else:
                flash('Incorrect Password', 'fail')
                return redirect(url_for('user', user_id=user_id))

        if newpfp:
            if newpfp.filename != '':
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)

                filename = newpfp.filename  
                filepath = os.path.join(upload_folder, filename)

                img = Image.open(newpfp)
                max_width, max_height = 512, 512

                if img.width > max_width or img.height > max_height:
                    flash(f'Image Is Too Large, Max Size Is 512 x 512', 'fail')
                    return redirect(url_for('user', user_id=user_id))
                
                newpfp.stream.seek(0)
                newpfp.save(filepath)

                user.pfp = f"/static/uploads/{filename}"
                db.session.commit()
                flash('Profile Picture Updated Successfully', 'success')

            else:
                flash('No file selected', 'fail')

            return redirect(url_for('user', user_id=user_id))

        if newgoal:
            user.watergoal = int(newgoal)
            db.session.commit()
            flash('Goal Updated Successfully', 'success')
            return redirect(url_for('user', user_id=user_id))

        if oldpass and newpass:
            if bcrypt.check_password_hash(current_user.password, oldpass):
                current_user.password = bcrypt.generate_password_hash(newpass).decode('utf-8')
                db.session.commit()
                flash('Password Updated Successfully', 'success')
                return redirect(url_for('user', user_id=user_id))
            else:
                flash('Incorrect Password', 'fail')
                return redirect(url_for('user', user_id=user_id))

        if deletepass and confirmpass:
            if deletepass == confirmpass:
                if bcrypt.check_password_hash(user.password, deletepass):
                    db.session.delete(user)
                    db.session.commit()
                    logout_user()
                    flash('Account Deleted Successfully', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Incorrect Password', 'fail')
                    return redirect(url_for('user', user_id=user_id))
            else:
                flash('Passwords Do Not Match', 'fail')
                return redirect(url_for('user', user_id=user_id))

# Run

if __name__ == '__main__':
    app.run(debug=True)