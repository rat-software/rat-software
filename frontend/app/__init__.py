import os
from flask import Flask, render_template
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_security import Security, SQLAlchemyUserDatastore
from flask_mail import Mail
from app.forms import ExtendedRegisterForm, ExtendedSendConfirmationForm, ExtendedForgotPasswordForm

# ... (db, migrate, security, mail Objekte erstellen) ...
db = SQLAlchemy(metadata=MetaData(naming_convention={
    'pk': 'pk_%(table_name)s', 'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'ix': 'ix_%(table_name)s_%(column_0_name)s', 'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s'
}))
migrate = Migrate()
security = Security()
mail = Mail()


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)

from app.models import User, Role
user_datastore = SQLAlchemyUserDatastore(db, User, Role)

security.init_app(
    app,
    user_datastore,
    register_form=ExtendedRegisterForm,
    confirm_register_form=ExtendedRegisterForm,
    send_confirmation_form=ExtendedSendConfirmationForm,
    forgot_password_form=ExtendedForgotPasswordForm
    # Die Zeile 'register_email_subject' wurde hier entfernt
)

# ... (Fehler-Handler und Routen-Imports bleiben gleich) ...
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

from .views import (dashboard, evaluation, study, question,
                    assessment, analysis, participant, export, scraper, query, query_sampler, url_filters)