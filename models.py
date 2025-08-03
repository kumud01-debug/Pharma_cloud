from database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    designation = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed password

class PharmaRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add your fields here later (for warehouse, QC, etc.)
