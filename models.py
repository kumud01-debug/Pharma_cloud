from database import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    designation = db.Column(db.String(50), nullable=False)  # Department: QC, QA, etc.
    position = db.Column(db.String(50), nullable=False)     # QC Officer, Sr. Officer, etc.
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)         # 'admin' or 'staff'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class QCRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_no = db.Column(db.String(50))
    result = db.Column(db.String(255))
    status = db.Column(db.String(50))  # pass/fail
    uploaded_by = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

# More models: WarehouseStock, ProductionBatch, QAReport, etc.
