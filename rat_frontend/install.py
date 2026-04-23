import os
import sys
from datetime import datetime, timezone
from getpass import getpass
from flask_security.utils import hash_password
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def check_db_config():
    """Checks if the database connection string exists in the environment."""
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if not db_uri or db_uri == 'postgresql://user:password@ip/db':
        print("====================================================")
        print("   HINT: DATABASE CONNECTION NOT CONFIGURED         ")
        print("====================================================")
        print("Your .env file is missing the SQLALCHEMY_DATABASE_URI.")
        print("Please add your PostgreSQL connection string to your .env file:")
        print("\nExample:")
        print("SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/rat_db")
        print("\nNote: Ensure you have created the database and applied")
        print("migrations before running this installer.")
        print("====================================================")
        sys.exit(1)

# Perform the check immediately
check_db_config()

# Now try to import app and models
try:
    from app import app, db 
    from models import User
except ImportError as e:
    print(f"Error: Could not import app or models. Ensure your virtualenv is active and project structure is correct. {e}")
    sys.exit(1)

def run_installation():
    print("====================================================")
    print("   RAT SOFTWARE INITIAL SETUP - CREATE SUPER ADMIN  ")
    print("====================================================")
    
    # Get user input
    email = input("Enter Super Admin Email: ").strip()
    if not email:
        print("Error: Email cannot be empty.")
        sys.exit(1)

    password = getpass("Enter Super Admin Password (input hidden): ")
    if len(password) < 8:
        print("Error: Password should be at least 8 characters long.")
        sys.exit(1)

    confirm_password = getpass("Confirm Password: ")
    if password != confirm_password:
        print("Error: Passwords do not match.")
        sys.exit(1)

    # Database operation within application context
    with app.app_context():
        print(f"Connecting to database at: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"Error: A user with email '{email}' already exists.")
                sys.exit(1)

            # Create the Super Admin user
            print("Creating Super Admin account...")
            new_admin = User(
                email=email,
                username=email,             # Username matches email as requested
                password=hash_password(password),
                active=True,
                confirmed_at=datetime.now(timezone.utc),
                super_admin=True            # Set the boolean flag
            )

            db.session.add(new_admin)
            db.session.commit()
            
            print("----------------------------------------------------")
            print(f"SUCCESS: Super Admin '{email}' created successfully.")
            print("You can now log in to the system.")
            print("----------------------------------------------------")

        except Exception as e:
            print(f"CRITICAL ERROR: Could not access database tables. {e}")
            print("Hint: Did you run 'flask db upgrade' to create the tables?")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    run_installation()