from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    admin = User(
        user_id='admin01',
        designation='Admin',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )

    db.session.add(admin)
    db.session.commit()

    user = User.query.filter_by(user_id='admin01').first()
    print("✅ Found user in DB:" if user else "❌ User not found")
    print(user.user_id if user else "No user")
