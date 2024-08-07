# Initialize Flask

from flask import Flask
from flask_simplelogin import SimpleLogin

# Create a new Flask application instance
app = Flask(__name__)

# Configure the application with a secret key
# This key is used for session management and should be kept secret
app.config["SECRET_KEY"] = "4012d0be-dcd6-4773-b866-c6f48959a4aa,"

# Initialize SimpleLogin for handling user authentication
SimpleLogin(app)

# Import routes after initializing the app
# This ensures that the routes are properly registered with the app
from app import routes
