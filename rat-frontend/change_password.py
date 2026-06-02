from app import app, db
from app.models import User
from flask_security.utils import hash_password

# Wrap everything inside the application context
with app.app_context():
    user = User.query.filter_by(email="sebastian.suenkler@gmx.de").first()

    if user:
        user.password = hash_password("TemporaryPassword123!")
        user.force_password_change = True
        db.session.commit()
        print("🎉 Success! Sebastian's password reset. Force-change flag engaged.")
    else:
        print("❌ User not found.")