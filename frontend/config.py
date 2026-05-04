import os

# Get the absolute path to the directory containing this file
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """
    Configuration class for the application.

    This class contains configuration variables for the application, including
    settings for the database, security, email, and other application-related
    features.
    """
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'postgresql://rat:6n9TYHN@85.214.110.132/rat3'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True  # Ensures connections are valid before use
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disables modification tracking for performance

    # Application debug mode
    DEBUG = True  # Set to True for debugging; should be False in production

    # Secret key for securing sessions and cookies
    SECRET_KEY = 'xzjpsV4WupS2cyH1Q5zGvu0JWy0T_PX8q5lqdhqx4ik'

    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get(
        'SECURITY_PASSWORD_SALT',
        '105214450030549024746975179922129984153'
    )  # Salt for hashing passwords, can be overridden by environment variable

    REMEMBER_COOKIE_SAMESITE = 'strict'  # Controls cross-site cookie behavior
    SESSION_COOKIE_SAMESITE = 'strict'   # SameSite policy for session cookies

    # Security features configuration
    SECURITY_REGISTERABLE = True  # Allows user registration
    SECURITY_CONFIRMABLE = False  # Requires email confirmation for registration
    SECURITY_RECOVERABLE = True  # Allows password recovery
    SECURITY_TRACKABLE = True  # Enables tracking of user sessions
    SECURITY_CHANGEABLE = True  # Allows password changes
    SECURITY_LOGIN_USER_TEMPLATE = '/security/login_user.html'  # Template for login

    # Views to redirect to after specific security actions
    SECURITY_POST_LOGIN_VIEW = '/tool_selection'
    SECURITY_POST_LOGOUT_VIEW = '/home'
    SECURITY_POST_REGISTER_VIEW = '/login_redirect/'

    # Advanced security settings
    SECURITY_UNIFIED_SIGNIN = False  # If True, uses a unified sign-in approach
    SECURITY_TWO_FACTOR = False  # If True, enables two-factor authentication
    SECURITY_MULTI_FACTOR_RECOVERY_CODES = False  # If True, enables multi-factor recovery codes
    SECURITY_USERNAME_ENABLE = False  # If True, username is used for login
    SECURITY_US_ENABLED_METHODS = []  # List of enabled user authentication methods

    # Security messages
    SECURITY_MSG_DISABLED_ACCOUNT = (
        'Your account has not yet been activated. We will contact you to discuss your requirements and then activate the account.', 
        'error'
    )

    # Email server configuration (commented out configuration should be removed or uncommented as needed)
    # MAIL_SERVER = 'smtp.mailtrap.io'
    # MAIL_PORT = 2525
    # MAIL_USERNAME = 'f1877e4bd680b6'
    # MAIL_PASSWORD = 'c02f3ebaa0fa41'
    # MAIL_USE_TLS = True
    # MAIL_USE_SSL = False

    MAIL_SERVER = 'server228.campusspeicher.de'
    MAIL_PORT = 465
    MAIL_USERNAME = 'rat@searchstudies.org'
    MAIL_PASSWORD = 'SearchHH1234'
    MAIL_USE_TLS = False  # Use TLS for email connection (False here)
    MAIL_USE_SSL = True   # Use SSL for email connection (True here)

    # Additional configuration options (commented out configurations should be reviewed)
    # SQLALCHEMY_ECHO = False  # If True, logs SQL queries
    # FLASK_ENV = 'development'  # Environment setting (development/production)

