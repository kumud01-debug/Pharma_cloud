from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import User  # Import your models here
from database import db
# -------------------
# App Configuration
# -------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharma_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'

# -------------------
# Database + Migration Setup
# -------------------
db.init_app(app)
migrate = Migrate(app, db)

# -------------------
# Routes
# -------------------

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
            return "Invalid credentials."

    return render_template("login.html")


@app.route("/admin")
def admin_panel():
    if "designation" in session and session["designation"] == "Admin":
        users = User.query.all()
        return render_template("admin_panel.html", users=users)
    return redirect(url_for("login"))


@app.route("/qc")
def qc_dashboard():
    return "Welcome to QC Dashboard"


@app.route("/warehouse")
def warehouse_dashboard():
    return "Welcome to Warehouse Dashboard"


@app.route("/production")
def production_dashboard():
    return "Welcome to Production Dashboard"


@app.route("/qa")
def qa_dashboard():
    return "Welcome to QA Dashboard"


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------
# CLI Command to Create Initial Admin
# -------------------
@app.cli.command("create-admin")
def create_admin():
    """Run this command to create an initial admin user."""
    if not User.query.filter_by(user_id="admin01").first():
        hashed_pw = generate_password_hash("admin123")
        admin_user = User(
            user_id="admin01",
            designation="Admin",
            position="Admin",
            role="admin",
            password=hashed_pw
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin01 / admin123")
    else:
        print("⚠️ Admin already exists.")


if __name__ == "__main__":
    app.run(debug=True)

