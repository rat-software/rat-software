import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mailman import Mail
from sqlalchemy import MetaData
from flask_migrate import Migrate
from config import Config
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password
from flask_security.models import fsqla_v3 as fsqla
from .forms import ExtendedRegisterForm

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)

convention = {
    'pk': 'pk_%(table_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'ix': 'ix_%(table_name)s_%(column_0_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s'
}
metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(app,
                metadata=metadata,
                session_options={'autocommit': False})

fsqla.FsModels.set_db_info(db)

from app import models
from app.models import User, Role

migrate = Migrate(app, db)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

# Create path for bootstrap files and custom css
@app.route('/static/<path:filename>')
def serve_bootstrap(filename):
    return app.send_static_file(filename)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('/errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('/errors/500.html'), 500


from .views import dashboard
from .views import evaluation
from .views import study
from .views import monitoring
from .views import question
from .views import assessment
from .views import analysis
from .views import participant
from .views import export
from .views import scraper
from .views import query
