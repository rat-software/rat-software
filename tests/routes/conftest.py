"""
Flask test fixtures für Route-Tests.

Lädt die echte rat-frontend-App mit einer In-Memory-SQLite-Datenbank,
ohne den echten PostgreSQL-Server zu benötigen.

Isolation: Dieses conftest.py liegt in tests/routes/ und beeinflusst
damit nur die Route-Tests, nicht die Unit-Tests in tests/*.py.
"""
import os
import sys

# rat-frontend muss importierbar sein, BEVOR die App geladen wird,
# damit load_dotenv() die Umgebungsvariablen nicht überschreibt.
_RAT_FRONTEND = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'rat-frontend')
)
sys.path.insert(0, _RAT_FRONTEND)

os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ.setdefault('SECRET_KEY',             'test-secret-key-not-for-prod')
os.environ.setdefault('SECURITY_PASSWORD_SALT', 'test-password-salt')
os.environ.setdefault('API_UPLOAD_KEY',         'test-api-key')
os.environ.setdefault('STORAGE_BASE_URL',       'http://localhost')

import pytest
from datetime import datetime
from sqlalchemy.pool import StaticPool

from app import app as flask_app, db


@pytest.fixture(scope='session')
def app():
    # StaticPool keeps a single SQLite connection alive for all operations,
    # which prevents the in-memory database from being reset between requests.
    flask_app.config.update({
        'TESTING':                          True,
        'WTF_CSRF_ENABLED':                 False,
        'SECURITY_WTF_CSRF_ENABLED':        False,
        'SECURITY_CSRF_PROTECT_MECHANISMS': [],
        'SECURITY_CONFIRMABLE':             False,
        'SECURITY_SEND_REGISTER_EMAIL':     False,
        'MAIL_SUPPRESS_SEND':               True,
        'RECAPTCHA_BYPASS':                 True,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
        },
    })

    # Set up DB in a scoped context, then close it.
    # Keeping the app context open for the whole session would cause Flask-Login
    # to cache g._login_user in the shared app context, leaking auth state
    # between tests that use auth_client and tests that use plain client.
    with flask_app.app_context():
        db.create_all()
        _seed_db()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


def _seed_db():
    from app.models import User, Role, QuestionType
    from flask_security import hash_password

    role = Role(name='Admin', description='', update_datetime=datetime.now(), permissions='')
    db.session.add(role)
    db.session.flush()

    user = User(
        email='admin@example.com',
        password=hash_password('Test1234!'),
        active=True,
        confirmed_at=datetime.now(),
        fs_uniquifier='test-uniquifier-routes-abc123',
    )
    user.roles.append(role)
    db.session.add(user)

    for display, name in [
        ('short_text',      'Short Text'),
        ('long_text',       'Long Text'),
        ('true_false',      'True/False'),
        ('likert_scale',    'Likert Scale'),
        ('multiple_choice', 'Multiple Choice'),
        ('scale_number',    'Scale (Number)'),
    ]:
        db.session.add(QuestionType(display=display, name=name))

    db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Eingeloggter Test-Client (Admin-User)."""
    r = client.post('/login', data={
        'email':    'admin@example.com',
        'password': 'Test1234!',
    }, follow_redirects=False)
    assert r.status_code == 302, f"Login fehlgeschlagen: {r.status_code}"
    return client


@pytest.fixture
def study_id(app):
    """Erstellt eine Teststudie in der DB und gibt deren ID zurück.

    Absichtlich kein auth_client-Dependency: Participant-Tests brauchen
    einen nicht-eingeloggten Client und dürfen nicht versehentlich
    durch die auth_client-Fixture eingeloggt werden.
    """
    from app.models import Study, User

    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        study = Study(
            name='Route Test Study',
            description='Test description',
            status=0,
            result_count=10,
            created_at=datetime.now(),
            live_link_mode=True,
            visible=True,
        )
        study.users.append(user)
        db.session.add(study)
        db.session.commit()
        sid = study.id

    yield sid

    with app.app_context():
        s = db.session.get(Study, sid)
        if s:
            db.session.delete(s)
            db.session.commit()


@pytest.fixture
def participant_id(app, study_id):
    """Erstellt einen Teilnehmer, der der Teststudie zugeordnet ist."""
    from app.models import Participant, Study

    with app.app_context():
        study = db.session.get(Study, study_id)
        p = Participant(
            name='testuser_fixture',
            password=4242,
            created_at=datetime.now(),
        )
        p.studies.append(study)
        db.session.add(p)
        db.session.commit()
        pid = p.id

    yield pid

    with app.app_context():
        from app.models import Participant
        p = db.session.get(Participant, pid)
        if p:
            db.session.delete(p)
            db.session.commit()


@pytest.fixture
def question_id(app, study_id):
    """Erstellt eine Frage in der Teststudie."""
    from app.models import Question, Study, QuestionType

    with app.app_context():
        qt = QuestionType.query.filter_by(display='short_text').first()
        study = db.session.get(Study, study_id)
        q = Question(
            title='Test Question',
            position=1,
            study=study,
            questiontype=qt,
        )
        db.session.add(q)
        db.session.commit()
        qid = q.id

    yield qid

    with app.app_context():
        from app.models import Question
        q = db.session.get(Question, qid)
        if q:
            db.session.delete(q)
            db.session.commit()


@pytest.fixture
def query_id(app, study_id):
    """Erstellt eine löschbare Query (source_type='manual', keine Ergebnisse)."""
    from app.models import Query

    with app.app_context():
        q = Query(
            query='test keyword',
            study_id=study_id,
            limit=10,
            source_type='manual',
        )
        db.session.add(q)
        db.session.commit()
        qid = q.id

    yield qid

    with app.app_context():
        q = db.session.get(Query, qid)
        if q:
            db.session.delete(q)
            db.session.commit()
