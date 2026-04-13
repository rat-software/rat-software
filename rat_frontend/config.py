import os

class Config(object):
    """
    Central configuration class for the Flask application.
    
    This class defines database connections, security settings, mail server 
    configurations, and external service keys used across the platform.
    """

    # --- Core Application Security ---
    # Secret key for signing session cookies and protection against CSRF
    SECRET_KEY = ''

    # --- Database Configuration ---
    # Connection string for the PostgreSQL production database
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@ip/db'
    
    # Disable tracking overhead for performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ensure the engine checks the connection health before executing queries
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    
    # --- Environment Settings ---
    # Active debug mode for development (Disable in production)
    DEBUG = False

    # --- URL Generation Settings ---
    # Necessary for generating absolute URLs (e.g., in password reset emails)
    #SERVER_NAME = 'tool.rat-software.org'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'

    # --- reCAPTCHA Configuration ---
    # Keys for validating human users in forms
    RECAPTCHA_PUBLIC_KEY = ''

    # --- Email Service (Resend) ---
    # API key for direct interaction with Resend email service
    RESEND_API_KEY = ''

    # SMTP configuration for Flask-Mail via Resend
    MAIL_SERVER = 'smtp.resend.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'resend'
    MAIL_PASSWORD = ''
    
    # --- Flask-Security-Too Configuration ---
    # Salt used for hashing security-related tokens (confirmations, resets)
    SECURITY_PASSWORD_SALT = ''
    
    # Default 'From' address for all automated system emails
    SECURITY_EMAIL_SENDER = ''

    # Enable core security features for user management
    SECURITY_REGISTERABLE = True  # Allows new users to sign up
    SECURITY_CONFIRMABLE  = True  # Requires email verification
    SECURITY_RECOVERABLE  = True  # Enables password reset via email
    SECURITY_TRACKABLE    = True  # Logs login count, IP addresses, etc.
    SECURITY_CHANGEABLE   = True  # Allows users to change passwords while logged in

    # UI Customization and Post-Action Redirects
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
    SECURITY_POST_LOGIN_VIEW = '/'
    SECURITY_POST_LOGOUT_VIEW = '/'

    # --- Storage and File Management ---
    STORAGE_FOLDER = '' # Absolute path to the directory where scraped sources are permanently stored (e.g., "/var/www/storage")
    
    # Shared secret for authenticating file uploads from the scraper service
    API_UPLOAD_KEY = ''
    
    # Public base URL for accessing stored files and media
    STORAGE_BASE_URL = ''

    API_URL = '' # Public base URL for accessing stored files and media (e.g., "https://your_domain/storage")

    SECURITY_MSG_CONFIRMATION_REQUEST = (
    'A confirmation email has just been sent to %(email)s. Please check your inbox.', 
    'info'
)

SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED = (
    'The email address %(email)s is already registered in our system.', 
    'error'
)

SECURITY_MSG_EMAIL_CONFIRMED = (
    'Thank you! Your email address has been successfully confirmed. You can now log in.', 
    'success'
)

SECURITY_MSG_ALREADY_CONFIRMED = (
    'Your email address has already been confirmed.', 
    'info'
)


# --- Password Reset Messages ---
SECURITY_MSG_PASSWORD_RESET_REQUEST = (
    'Instructions to reset your password have been sent to %(email)s.', 
    'info'
)

SECURITY_MSG_PASSWORD_RESET = (
    'You successfully changed your password.', 
    'success'
)

SECURITY_MSG_INVALID_RESET_PASSWORD_TOKEN = (
    'Invalid or expired password reset token.', 
    'error'
)

SECURITY_MSG_PASSWORD_IS_THE_SAME = (
    'Your new password must be different from your previous password.', 
    'error'
)


# --- Login Error Messages ---
SECURITY_MSG_USER_DOES_NOT_EXIST = (
    'The specified user does not exist.', 
    'error'
)

SECURITY_MSG_INVALID_PASSWORD = (
    'Invalid password.', 
    'error'
)

SECURITY_MSG_UNCONFIRMED_ACCOUNT = (
    'Your email address requires confirmation before logging in. Please check your inbox.', 
    'error'
)

SECURITY_MSG_DISABLED_ACCOUNT = (
    'This account has been disabled.', 
    'error'
)