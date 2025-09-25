import os

class Config(object):
    """
    Zentrale Konfigurationsklasse für die Flask-Anwendung.
    """
    # --- Geheimer Schlüssel ---
    SECRET_KEY = 'your_secret_key'

    # --- Datenbank-Konfiguration ---
    SQLALCHEMY_DATABASE_URI = 'postgresql://rat:your_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    
    # --- App-Modus ---
    DEBUG = True

    # --- Server Name & URLSchema ---
    SERVER_NAME = 'your_server_name'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'

    # --- reCAPTCHA Konfiguration ---
    RECAPTCHA_PUBLIC_KEY = 'your_public_key'
    RECAPTCHA_PRIVATE_KEY = 'your_private_key'

    RESEND_API_KEY = 'your_resend_api_key'



    # --- Flask-Mail Konfiguration für den Versand über RESEND SMTP ---
    MAIL_SERVER = 'smtp.resend.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'resend'
    MAIL_PASSWORD = 'your_resend_password'
    
    SECURITY_PASSWORD_SALT = 'your_salt'
    
    SECURITY_EMAIL_SENDER = 'your_mail'

    # Features aktivieren
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True

    # Templates und Umleitungen
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
    SECURITY_POST_LOGIN_VIEW = '/'
    SECURITY_POST_LOGOUT_VIEW = '/home'