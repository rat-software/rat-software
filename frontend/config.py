import os
basedir = os.path.abspath(os.path.dirname(__file__))
database_uri = 'postgresql://your_db_user:your_db_password@your_db_host/your_db_name'

class Config(object):
    SQLALCHEMY_DATABASE_URI = database_uri
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True,}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = True

    SECRET_KEY = 'xzjpsV4WupS2cyH1Q5zGvu0JWy0T_PX8q5lqdhqx4ik'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', '105214450030549024746975179922129984153')

    REMEMBER_COOKIE_SAMESITE = 'strict'
    SESSION_COOKIE_SAMESITE = 'strict'

    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_LOGIN_USER_TEMPLATE = '/security/login_user.html'
    #SECURITY_LOGIN_USER_TEMPLATE = '/security/register_user.html'

    SECURITY_POST_LOGIN_VIEW = '/'
    SECURITY_POST_LOGOUT_VIEW = '/home'

    SECURITY_UNIFIED_SIGNIN = False
    SECURITY_TWO_FACTOR = False
    SECURITY_MULTI_FACTOR_RECOVERY_CODES = False
    SECURITY_USERNAME_ENABLE = False
    SECURITY_US_ENABLED_METHODS = []

    #MAIL_SERVER = 'smtp.mailtrap.io'
    #MAIL_PORT = 2525
    #MAIL_USERNAME = 'f1877e4bd680b6'
    #MAIL_PASSWORD = 'c02f3ebaa0fa41'
    #MAIL_USE_TLS = True
    #MAIL_USE_SSL = False

    MAIL_SERVER = 'your_mail_server'
    MAIL_PORT = 465
    MAIL_USERNAME = 'your_mail_username'
    MAIL_PASSWORD = 'your_mail_password'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    # SQLALCHEMY_ECHO = False
    # FLASK_ENV = 'development'
