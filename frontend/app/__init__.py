import os
from flask import Flask, render_template
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_security import Security, SQLAlchemyUserDatastore

# Configure SQLAlchemy with custom metadata naming conventions
db = SQLAlchemy(metadata=MetaData(naming_convention={
    'pk': 'pk_%(table_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'ix': 'ix_%(table_name)s_%(column_0_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s'
}))

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from Config class

# Initialize Flask-Mail for email sending
mail = Mail(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

# Initialize SQLAlchemy with Flask app
db.init_app(app)

# Import user and role models
from app.models import User, Role

# Set up Flask-Security for user authentication and authorization
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route('/static/<path:filename>')
def serve_bootstrap(filename):
    """
    Serve static files from the 'static' directory.

    Args:
        filename (str): The path to the static file.

    Returns:
        Response: The static file to be served.
    """
    return app.send_static_file(filename)

@app.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 Not Found errors.

    Args:
        e (Exception): The exception raised.

    Returns:
        tuple: A response with a 404 status code and a rendered error page.
    """
    return render_template('/errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """
    Handle 500 Internal Server Error.

    Args:
        e (Exception): The exception raised.

    Returns:
        tuple: A response with a 500 status code and a rendered error page.
    """
    return render_template('/errors/500.html'), 500

# Import and register blueprints (if needed)
# from app.views import register_blueprints
# register_blueprints(app)

# Import view modules to register routes
from .views import (dashboard, evaluation, study, question, 
                    assessment, analysis, participant, export, scraper, query)

# Ensure that all imported view modules are registered correctly
