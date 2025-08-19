from database import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    designation = db.Column(db.String(50), nullable=False)  # Admin, QC, QA, etc.
    position = db.Column(db.String(50), nullable=False)     # Officer, Exec, HOD
    role = db.Column(db.String(50), nullable=False)         # admin, staff
    password_hash = db.Column(db.String(200), nullable=False)

# Example table for QC records
class QCRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Example table for Warehouse
class WarehouseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Example table for Production
class ProductionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_no = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Example table for QA
class QARecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audit_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# models.py
from datetime import datetime
from database import db

# --- Raw material master & QC artifacts ---

class RawMaterial(db.Model):
    __tablename__ = "raw_material"
    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(50), nullable=False, index=True)
    material_name = db.Column(db.String(200), nullable=False)
    lot_no = db.Column(db.String(100), nullable=False, index=True)
    vendor = db.Column(db.String(200))
    received_qty = db.Column(db.Float)  # keep numeric for analytics
    unit = db.Column(db.String(20))
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="Pending Sampling")  # Pending Sampling | Sampled | Testing | Pass | Fail

    # relationships
    samples = db.relationship("QCSample", backref="material", lazy=True, cascade="all, delete-orphan")
    specs = db.relationship("Specification", backref="material", lazy=True, cascade="all, delete-orphan")

    # convenience
    def latest_sample(self):
        return sorted(self.samples, key=lambda s: s.sample_date or datetime.min, reverse=True)[0] if self.samples else None


class QCSample(db.Model):
    __tablename__ = "qc_sample"
    id = db.Column(db.Integer, primary_key=True)
    ar_no = db.Column(db.String(40), unique=True, index=True)  # e.g., AR-20250812-0001
    sample_date = db.Column(db.DateTime, default=datetime.utcnow)
    sampler = db.Column(db.String(100))  # user_id or name
    remarks = db.Column(db.Text)

    material_id = db.Column(db.Integer, db.ForeignKey("raw_material.id"), nullable=False)

    # relationships
    results = db.relationship("TestResult", backref="sample", lazy=True, cascade="all, delete-orphan")
    coa = db.relationship("COA", uselist=False, backref="sample", cascade="all, delete-orphan")


class Specification(db.Model):
    __tablename__ = "specification"
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("raw_material.id"), nullable=False)

    parameter = db.Column(db.String(120), nullable=False)     # e.g., "pH", "Assay"
    method = db.Column(db.String(120))                        # e.g., "USP <791>"
    unit = db.Column(db.String(40))                           # e.g., "pH units", "%", "ppm"
    lower_limit = db.Column(db.Float)                         # numeric lower (nullable)
    upper_limit = db.Column(db.Float)                         # numeric upper (nullable)
    textual_limit = db.Column(db.String(200))                 # e.g., "Complies", "Clear solution" (nullable)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TestResult(db.Model):
    __tablename__ = "test_result"
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("qc_sample.id"), nullable=False)

    parameter = db.Column(db.String(120), nullable=False)
    result_value = db.Column(db.Float)          # numeric result (nullable)
    result_text = db.Column(db.String(200))     # textual result (nullable)
    unit = db.Column(db.String(40))
    verdict = db.Column(db.String(10))          # Pass/Fail

    tested_by = db.Column(db.String(100))
    tested_at = db.Column(db.DateTime, default=datetime.utcnow)


class COA(db.Model):
    __tablename__ = "coa"
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("qc_sample.id"), nullable=False, unique=True)

    overall_verdict = db.Column(db.String(10))  # Pass/Fail
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
 
class WarehouseMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(100), nullable=False)
    material_code = db.Column(db.String(50), nullable=False)   # removed unique=True
    supplier_name = db.Column(db.String(100), nullable=False)
    quantity_received = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Received')

# Material issued to production
class WarehouseIssue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("warehouse_material.id"), nullable=False)
    issued_quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), default="kg")
    issued_to = db.Column(db.String(200), nullable=False)  # Production / QA / QC
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.String(300))

# Finished goods dispatch
class WarehouseDispatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    batch_no = db.Column(db.String(100), nullable=False)
    quantity_dispatched = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), default="boxes")
    customer_name = db.Column(db.String(200), nullable=False)
    dispatch_date = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.String(300))
