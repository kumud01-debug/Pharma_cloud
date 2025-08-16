from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()  # Create all tables

    if not User.query.filter_by(user_id='admin01').first():
        admin = User(
            user_id='admin01',
            designation='Admin',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully!")
    else:
        print("⚠️ Admin user already exists.")
