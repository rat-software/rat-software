import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config(object):
    # --- Core Application Security ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key-for-dev-only')

    # --- Database Configuration ---
    # The URL is read from .env; make sure it starts with 'postgresql://'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # --- Environment Settings ---
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # --- URL Generation Settings ---
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'

    # --- reCAPTCHA Configuration ---
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')

    # --- Email Service (Resend / SMTP) ---
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.resend.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'resend')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

    # --- Flask-Security-Too Configuration ---
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'default-salt')
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
    API_URL = os.environ.get('API_URL', '')