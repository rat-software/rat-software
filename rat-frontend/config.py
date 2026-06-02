import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config(object):
    """
    Central configuration class for the Flask application.
    All sensitive metrics and secrets are managed exclusively via the .env file.
    """

    # --- Core Application Security ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key-for-dev-only')

    # --- Database Configuration ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # --- Environment Settings ---
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # --- URL Generation Settings ---
    #SERVER_NAME = os.environ.get('SERVER_NAME')
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'

    # --- reCAPTCHA Configuration ---
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')

    # --- Email Service (Resend / SMTP) ---
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.resend.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'resend')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # --- Flask-Security-Too Configuration ---
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'fallback-salt')
    SECURITY_EMAIL_SENDER = os.environ.get('SECURITY_EMAIL_SENDER', 'noreply@yourdomain.com')

    # Security Features
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE  = True
    SECURITY_RECOVERABLE  = True
    SECURITY_TRACKABLE    = True
    SECURITY_CHANGEABLE   = True

    # Templates & Redirects
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
    SECURITY_POST_LOGIN_VIEW = '/'
    SECURITY_POST_LOGOUT_VIEW = '/'

    # --- Storage and File Management ---
    STORAGE_FOLDER = os.environ.get('STORAGE_FOLDER', '')
    API_UPLOAD_KEY = os.environ.get('API_UPLOAD_KEY', '')
    STORAGE_BASE_URL = os.environ.get('STORAGE_BASE_URL', '')

    # ==============================================================================
    # TRANSLATION & SYSTEM MESSAGES (No sensitive data here)
    # ==============================================================================
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