import os
import sys
from datetime import datetime, timezone
from getpass import getpass
from flask_security.utils import hash_password
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
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
        print("migrations before running this script.")
        print("====================================================")
        sys.exit(1)

# Perform the database configuration check immediately
check_db_config()

# Try to import the Flask app and the User model
try:
    from app import app, db 
    from app.models import User
except ImportError as e:
    print(f"Error: Could not import app or models. Ensure your virtualenv is active and project structure is correct. {e}")
    sys.exit(1)

def run_installation():
    """Main function to prompt for user details and create the account."""
    print("====================================================")
    print("             RAT SOFTWARE - ADD USER                ")
    print("====================================================")
    
    # Get basic user credentials
    email = input("Enter User Email: ").strip()
    if not email:
        print("Error: Email cannot be empty.")
        sys.exit(1)

    password = getpass("Enter User Password (input hidden): ")
    if len(password) < 8:
        print("Error: Password should be at least 8 characters long.")
        sys.exit(1)

    confirm_password = getpass("Confirm Password: ")
    if password != confirm_password:
        print("Error: Passwords do not match.")
        sys.exit(1)

    # Ask if the user should be a Super Admin
    # Accepts 'y', 'yes', 'j', 'ja' as affirmative inputs
    is_super_admin_input = input("Should this user be a super admin? (y/n): ").strip().lower()
    is_super_admin = is_super_admin_input in ['y', 'yes', 'j', 'ja']

    # Execute database operations within the application context
    with app.app_context():
        print(f"Connecting to database at: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        try:
            # Check if a user with this email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"Error: A user with email '{email}' already exists.")
                sys.exit(1)

            # Determine the role name for logging output
            role_name = "Super Admin" if is_super_admin else "Standard User"
            print(f"Creating {role_name} account...")
            
            # Create the new user object
            # Note: The fs_uniquifier is required by Flask-Security-Too
            new_user = User(
                email=email,
                username=email,
                password=hash_password(password),
                active=True,
                confirmed_at=datetime.now(timezone.utc),
                super_admin=is_super_admin,
                fs_uniquifier=uuid.uuid4().hex
            )

            # Insert the new user into the database
            db.session.add(new_user)
            db.session.commit()
            
            print("----------------------------------------------------")
            print(f"SUCCESS: {role_name} '{email}' created successfully.")
            print("You can now log in to the system.")
            print("----------------------------------------------------")

        except Exception as e:
            print(f"CRITICAL ERROR: Could not access database tables. {e}")
            print("Hint: Did you run 'flask db upgrade' to create the tables?")
            # Rollback the transaction in case of an error
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    run_installation()