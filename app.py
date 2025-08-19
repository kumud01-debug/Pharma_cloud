from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, QCRecord, WarehouseRecord, ProductionRecord, QARecord, RawMaterial, QCSample, Specification, TestResult, COA, WarehouseMaterial
from database import db
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharma_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'

db.init_app(app)
migrate = Migrate(app, db)

# ------------------- LOGIN -------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]

        user = User.query.filter_by(user_id=user_id).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.user_id
            session["designation"] = user.designation
            session["position"] = user.position
            session["role"] = user.role

            if user.designation == "Admin":
                return redirect(url_for("admin_panel"))
            elif user.designation == "QC":
                return redirect(url_for("qc_dashboard"))
            elif user.designation == "Warehouse":
                return redirect(url_for("warehouse_dashboard"))
            elif user.designation == "Production":
                return redirect(url_for("production_dashboard"))
            elif user.designation == "QA":
                return redirect(url_for("qa_dashboard"))
            else:
                return "No dashboard assigned for your designation."
        else:
            flash("❌ Invalid credentials!", "error")

    return render_template("login.html")

# ------------------- ADMIN -------------------
@app.route("/admin")
def admin_panel():
    if "designation" in session and session["designation"] == "Admin":
        users = User.query.all()
        return render_template("admin_panel.html", users=users)
    return redirect(url_for("login"))

@app.route("/admin/add_user", methods=["POST"])
def add_user():
    if "designation" in session and session["designation"] == "Admin":
        user_id = request.form.get("user_id")
        designation = request.form.get("designation")
        position = request.form.get("position")
        role = request.form.get("role")
        password = request.form.get("password")

        if User.query.filter_by(user_id=user_id).first():
            flash("⚠️ User ID already exists!", "error")
            return redirect(url_for("admin_panel"))

        hashed_pw = generate_password_hash(password)
        new_user = User(
            user_id=user_id,
            designation=designation,
            position=position,
            role=role,
            password_hash=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()
        flash("✅ User added successfully!", "success")

    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    if "designation" in session and session["designation"] == "Admin":
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash("🗑 User deleted successfully!", "success")
    return redirect(url_for("admin_panel"))

# ------------------- QC -------------------


# ------------------ Helpers ------------------

def require_qc_or_admin():
    # simple gate
    if not session.get("user_id"):
        return False
    return session.get("designation") in ("QC", "Admin")

def next_ar_no():
    # AR-YYYYMMDD-#### per day sequence
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"AR-{today}-"
    latest = QCSample.query.filter(QCSample.ar_no.like(f"{prefix}%")) \
                           .order_by(QCSample.ar_no.desc()).first()
    if latest:
        last_seq = int(latest.ar_no.split("-")[-1])
        return f"{prefix}{last_seq+1:04d}"
    return f"{prefix}0001"

# ------------------ QC: Dashboard ------------------

@app.route("/qc_dashboard")
def qc_dashboard():
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    mats = RawMaterial.query.order_by(RawMaterial.received_date.desc()).all()
    return render_template("qc_dashboard.html", materials=mats)

# ------------------ QC: Create / Receive Material (for demo) ------------------
# In real life this comes from Warehouse. Here we give QC a quick way to seed materials.

@app.route("/qc/material/new", methods=["GET", "POST"])
def qc_new_material():
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    if request.method == "POST":
        rm = RawMaterial(
            material_code=request.form["material_code"],
            material_name=request.form["material_name"],
            lot_no=request.form["lot_no"],
            vendor=request.form.get("vendor"),
            received_qty=float(request.form.get("received_qty", 0) or 0),
            unit=request.form.get("unit"),
            status="Pending Sampling"
        )
        db.session.add(rm)
        db.session.commit()
        flash("✅ Material added.", "success")
        return redirect(url_for("qc_dashboard"))
    return render_template("qc_new_material.html")

# ------------------ QC: Material detail ------------------

@app.route("/qc/material/<int:material_id>")
def qc_material_detail(material_id):
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    m = RawMaterial.query.get_or_404(material_id)
    sample = m.latest_sample()
    specs = Specification.query.filter_by(material_id=material_id).all()
    results = TestResult.query.filter(TestResult.sample_id == (sample.id if sample else None)).all() if sample else []
    return render_template("qc_material_detail.html", m=m, sample=sample, specs=specs, results=results)

# ------------------ QC: Sampling / AR generation ------------------

@app.route("/qc/material/<int:material_id>/sample", methods=["POST"])
def qc_take_sample(material_id):
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    m = RawMaterial.query.get_or_404(material_id)
    ar = next_ar_no()
    s = QCSample(
        ar_no=ar,
        sampler=session.get("user_id"),
        remarks=request.form.get("remarks"),
        material=m
    )
    m.status = "Sampled"
    db.session.add(s)
    db.session.commit()
    flash(f"✅ Sample taken. AR No: {ar}", "success")
    return redirect(url_for("qc_material_detail", material_id=material_id))

# ------------------ QC: Specification CRUD (minimal add) ------------------

@app.route("/qc/material/<int:material_id>/spec/add", methods=["POST"])
def qc_add_spec(material_id):
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    m = RawMaterial.query.get_or_404(material_id)

    lower = request.form.get("lower_limit")
    upper = request.form.get("upper_limit")
    spec = Specification(
        material=m,
        parameter=request.form["parameter"],
        method=request.form.get("method"),
        unit=request.form.get("unit"),
        lower_limit=float(lower) if lower else None,
        upper_limit=float(upper) if upper else None,
        textual_limit=request.form.get("textual_limit")
    )
    db.session.add(spec)
    db.session.commit()
    flash("✅ Specification added.", "success")
    return redirect(url_for("qc_material_detail", material_id=material_id))

# ------------------ QC: Enter Test Result ------------------

def _judge_result(parameter, value_num, value_text, unit, specs_for_param):
    """
    Compare a result to matching spec rows. If any matching spec exists:
      - If textual_limit set → compare case-insensitive exact match.
      - Else use numeric range [lower_limit, upper_limit].
    Returns "Pass" or "Fail".
    """
    for s in specs_for_param:
        if s.textual_limit:
            if value_text and value_text.strip().lower() == s.textual_limit.strip().lower():
                return "Pass"
            else:
                return "Fail"
        else:
            if value_num is None:
                return "Fail"
            lo = s.lower_limit if s.lower_limit is not None else float("-inf")
            hi = s.upper_limit if s.upper_limit is not None else float("inf")
            if lo <= value_num <= hi:
                return "Pass"
            return "Fail"
    # no spec → conservative choice is Fail (or mark "NA")
    return "Fail"

@app.route("/qc/sample/<int:sample_id>/result/add", methods=["POST"])
def qc_add_result(sample_id):
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    s = QCSample.query.get_or_404(sample_id)
    m = s.material

    parameter = request.form["parameter"]
    unit = request.form.get("unit")
    val_num = request.form.get("result_value")
    val_text = request.form.get("result_text")

    value_num = float(val_num) if val_num not in (None, "",) else None
    specs = Specification.query.filter_by(material_id=m.id, parameter=parameter).all()

    verdict = _judge_result(parameter, value_num, val_text, unit, specs)

    tr = TestResult(
        sample=s,
        parameter=parameter,
        result_value=value_num,
        result_text=val_text,
        unit=unit,
        verdict=verdict,
        tested_by=session.get("user_id")
    )
    m.status = "Testing"
    db.session.add(tr)
    db.session.commit()
    flash(f"🧪 Result saved ({parameter}: {verdict}).", "success")
    return redirect(url_for("qc_material_detail", material_id=m.id))

# ------------------ QC: Generate COA (also sets overall status) ------------------

@app.route("/qc/sample/<int:sample_id>/generate_coa", methods=["POST"])
def qc_generate_coa(sample_id):
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    s = QCSample.query.get_or_404(sample_id)
    m = s.material
    results = TestResult.query.filter_by(sample_id=sample_id).all()
    if not results:
        flash("⚠️ No results found to generate COA.", "error")
        return redirect(url_for("qc_material_detail", material_id=m.id))

    overall = "Pass" if all(r.verdict == "Pass" for r in results) else "Fail"

    if s.coa:
        s.coa.overall_verdict = overall
        s.coa.generated_at = datetime.utcnow()
    else:
        db.session.add(COA(sample=s, overall_verdict=overall))

    m.status = overall
    db.session.commit()
    flash(f"📄 COA generated. Overall: {overall}", "success")
    return redirect(url_for("qc_view_coa", sample_id=sample_id))

@app.route("/qc/coa/<int:sample_id>")
def qc_view_coa(sample_id):
    if not require_qc_or_admin():
        return redirect(url_for("login"))
    s = QCSample.query.get_or_404(sample_id)
    m = s.material
    specs = Specification.query.filter_by(material_id=m.id).all()
    results = TestResult.query.filter_by(sample_id=sample_id).all()
    return render_template("qc_coa.html", m=m, s=s, specs=specs, results=results, coa=s.coa)


# ------------------- Warehouse -------------------
@app.route("/warehouse", methods=["GET", "POST"])
def warehouse_dashboard():
    if request.method == "POST":
        material_name = request.form["material_name"]
        quantity = request.form["quantity"]
        new_record = WarehouseRecord(material_name=material_name, quantity=quantity)
        db.session.add(new_record)
        db.session.commit()
    records = WarehouseRecord.query.all()
    return render_template("warehouse_dashboard.html", records=records)
    
    
# -------------------
# Warehouse Dashboard
# -------------------
# Add material (Receiving)
@app.route("/warehouse/add_material", methods=["POST"])
@app.route('/warehouse/add', methods=['POST'])
@app.route('/warehouse/add', methods=['POST'])
def add_material():
    material_code = request.form['material_code']
    existing = WarehouseMaterial.query.filter_by(material_code=material_code).first()
    if existing:
        return "⚠️ Material code already exists. Use a different code.", 400

    new_material = WarehouseMaterial(
        material_name=request.form['material_name'],
        material_code=material_code,
        supplier_name=request.form['supplier_name'],
        quantity_received=float(request.form['quantity_received']),
        unit=request.form['unit']
    )
    db.session.add(new_material)
    db.session.commit()
    return redirect('/warehouse')



# Issue material
@app.route("/warehouse/issue", methods=["POST"])
def issue_material():
    material_id = int(request.form.get("material_id"))
    issued_quantity = float(request.form.get("issued_quantity"))
    issued_to = request.form.get("issued_to")
    remarks = request.form.get("remarks")

    new_issue = WarehouseIssue(
        material_id=material_id,
        issued_quantity=issued_quantity,
        issued_to=issued_to,
        remarks=remarks
    )
    db.session.add(new_issue)

    # Update stock
    material = WarehouseMaterial.query.get(material_id)
    material.quantity_received -= issued_quantity
    db.session.commit()

    flash("📦 Material issued successfully!", "success")
    return redirect(url_for("warehouse_dashboard"))

# Dispatch finished goods
@app.route("/warehouse/dispatch", methods=["POST"])
def dispatch_goods():
    product_name = request.form.get("product_name")
    batch_no = request.form.get("batch_no")
    quantity_dispatched = float(request.form.get("quantity_dispatched"))
    customer_name = request.form.get("customer_name")
    remarks = request.form.get("remarks")

    new_dispatch = WarehouseDispatch(
        product_name=product_name,
        batch_no=batch_no,
        quantity_dispatched=quantity_dispatched,
        customer_name=customer_name,
        remarks=remarks
    )
    db.session.add(new_dispatch)
    db.session.commit()

    flash("🚚 Goods dispatched successfully!", "success")
    return redirect(url_for("warehouse_dashboard"))


# ------------------- Production -------------------
@app.route("/production", methods=["GET", "POST"])
def production_dashboard():
    if request.method == "POST":
        batch_no = request.form["batch_no"]
        status = request.form["status"]
        new_record = ProductionRecord(batch_no=batch_no, status=status)
        db.session.add(new_record)
        db.session.commit()
    records = ProductionRecord.query.all()
    return render_template("production_dashboard.html", records=records)

# ------------------- QA -------------------
@app.route("/qa", methods=["GET", "POST"])
def qa_dashboard():
    if request.method == "POST":
        audit_name = request.form["audit_name"]
        status = request.form["status"]
        new_record = QARecord(audit_name=audit_name, status=status)
        db.session.add(new_record)
        db.session.commit()
    records = QARecord.query.all()
    return render_template("qa_dashboard.html", records=records)

# ------------------- LOGOUT -------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------- CLI COMMAND -------------------
@app.cli.command("create-admin")
def create_admin():
    if not User.query.filter_by(user_id="admin01").first():
        hashed_pw = generate_password_hash("admin123")
        admin_user = User(
            user_id="admin01",
            designation="Admin",
            position="Admin",
            role="admin",
            password_hash=hashed_pw
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin01 / admin123")
    else:
        print("⚠️ Admin already exists.")

if __name__ == "__main__":
    app.run(debug=True)
