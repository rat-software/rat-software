from app import app, db
from app.models import User
from flask_security.utils import hash_password

# Wrap everything inside the application context
with app.app_context():
    user = User.query.filter_by(email="jutta.haider@hb.se").first()

    if user:
        user.password = hash_password("rat123!")
        user.force_password_change = True
        db.session.commit()
        print("🎉 Success! Force-change flag engaged.")
    else:
        print("❌ User not found.")