from database import db
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, PharmaRecord

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharma_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretkey123'

db.init_app(app)

@app.before_request
def create_tables_once():
    if not getattr(app, 'tables_created', False):
        db.create_all()
        app.tables_created = True

        # Create sample user only if no users exist
        if not User.query.first():
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash("12345")
            sample_user = User(user_id="admin01", designation="QC", password=hashed_password)
            db.session.add(sample_user)
            db.session.commit()
            print("✔ Sample user created")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        designation = request.form['designation']
        password = request.form['password']

        user = User.query.filter_by(user_id=user_id, designation=designation).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.user_id
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid login")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html', user=session['user'])
if __name__ == '__main__':
    app.run(debug=True)


