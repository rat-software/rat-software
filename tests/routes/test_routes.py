"""
Flask Route-Tests für rat-frontend.

Testet HTTP-Verhalten der Routen: Auth-Guards, CRUD, Status-Codes.
Benötigt keinen echten PostgreSQL-Server — läuft auf SQLite In-Memory.
"""
import pytest
from app import db


# ─────────────────────────────────────────────────────────────────────────────
# Unauthentifizierte Zugriffsversuche
# ─────────────────────────────────────────────────────────────────────────────

class TestUnauthenticatedRedirects:
    """Alle geschützten Routen leiten unauthentifizierte Requests zum Login um."""

    def test_root_redirects(self, client):
        r = client.get('/', follow_redirects=False)
        assert r.status_code == 302

    def test_dashboard_redirects_to_login(self, client):
        r = client.get('/dashboard', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_studies_redirects_to_login(self, client):
        r = client.get('/studies', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_study_new_redirects_to_login(self, client):
        r = client.get('/study/new', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_study_detail_redirects_to_login(self, client):
        r = client.get('/study/1', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_study_edit_redirects_to_login(self, client):
        r = client.get('/study/1/edit', follow_redirects=False)
        assert r.status_code == 302

    def test_study_delete_redirects_to_login(self, client):
        r = client.get('/study/1/delete', follow_redirects=False)
        assert r.status_code == 302

    def test_study_questions_redirects_to_login(self, client):
        r = client.get('/study/1/questions', follow_redirects=False)
        assert r.status_code == 302

    def test_study_queries_redirects_to_login(self, client):
        r = client.get('/study/1/queries', follow_redirects=False)
        assert r.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# Öffentliche Seiten
# ─────────────────────────────────────────────────────────────────────────────

class TestPublicRoutes:
    def test_contact_page_accessible_without_login(self, client):
        r = client.get('/contact')
        assert r.status_code == 200

    def test_contact_page_contains_form(self, client):
        r = client.get('/contact')
        assert b'form' in r.data.lower()

    def test_root_unauthenticated_lands_on_login(self, client):
        r = client.get('/', follow_redirects=True)
        assert r.status_code == 200
        assert b'login' in r.data.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Eingeloggt: Dashboard & Navigation
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthenticatedNavigation:
    def test_dashboard_returns_200(self, auth_client):
        r = auth_client.get('/dashboard')
        assert r.status_code == 200

    def test_root_authenticated_redirects_to_dashboard(self, auth_client):
        r = auth_client.get('/', follow_redirects=False)
        assert r.status_code == 302
        assert 'dashboard' in r.location

    def test_studies_list_returns_200(self, auth_client):
        r = auth_client.get('/studies')
        assert r.status_code == 200

    def test_new_study_form_returns_200(self, auth_client):
        r = auth_client.get('/study/new')
        assert r.status_code == 200

    def test_new_study_form_contains_name_field(self, auth_client):
        r = auth_client.get('/study/new')
        assert b'name' in r.data.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Eingeloggt: Studie erstellen
# ─────────────────────────────────────────────────────────────────────────────

class TestStudyCreate:
    def test_create_study_redirects_to_study_detail(self, auth_client):
        r = auth_client.post('/study/new/create/', data={
            'name': 'Created In Test',
            'description': '',
            'id': '0',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert '/study/' in r.location

    def test_create_study_with_description(self, auth_client):
        r = auth_client.post('/study/new/create/', data={
            'name': 'With Description',
            'description': 'Some text',
            'id': '0',
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_create_study_new_page_is_accessible_after_creation(self, auth_client):
        # Formular-GET nach einem POST-Redirect ist weiterhin zugänglich
        auth_client.post('/study/new/create/', data={'name': 'X', 'id': '0'})
        r = auth_client.get('/study/new')
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Eingeloggt: Studie lesen & bearbeiten
# ─────────────────────────────────────────────────────────────────────────────

class TestStudyDetail:
    def test_study_detail_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}')
        assert r.status_code == 200

    def test_study_detail_contains_study_name(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}')
        assert b'Route Test Study' in r.data

    def test_study_detail_404_for_nonexistent(self, auth_client):
        r = auth_client.get('/study/99999')
        assert r.status_code == 404

    def test_edit_study_form_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/edit')
        assert r.status_code == 200

    def test_edit_study_form_contains_study_name(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/edit')
        assert b'Route Test Study' in r.data

    def test_update_study_name_redirects(self, auth_client, study_id):
        r = auth_client.post('/study/new/create/', data={
            'name': 'Updated Name',
            'description': '',
            'id': str(study_id),
        }, follow_redirects=False)
        assert r.status_code == 302
        assert f'/study/{study_id}' in r.location

    def test_update_study_name_is_persisted(self, auth_client, study_id):
        auth_client.post('/study/new/create/', data={
            'name': 'Persisted Name',
            'description': '',
            'id': str(study_id),
        })
        r = auth_client.get(f'/study/{study_id}')
        assert b'Persisted Name' in r.data


# ─────────────────────────────────────────────────────────────────────────────
# Eingeloggt: Fragen & Queries
# ─────────────────────────────────────────────────────────────────────────────

class TestStudySubpages:
    def test_questions_page_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/questions')
        assert r.status_code == 200

    def test_queries_page_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/queries')
        assert r.status_code == 200

    def test_delete_study_get_shows_confirmation(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/delete')
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Eingeloggt: Studie löschen
# ─────────────────────────────────────────────────────────────────────────────

class TestStudyDelete:
    def test_delete_study_post_redirects(self, auth_client, app):
        from app.models import Study, User
        from datetime import datetime

        with app.app_context():
            user = User.query.filter_by(email='admin@example.com').first()
            s = Study(name='To Delete', status=0, result_count=10,
                      created_at=datetime.now(), live_link_mode=True, visible=True)
            s.users.append(user)
            db.session.add(s)
            db.session.commit()
            sid = s.id

        r = auth_client.post(f'/study/{sid}/delete', data={'submit': 'Confirm'}, follow_redirects=False)
        assert r.status_code == 302

    def test_deleted_study_returns_404(self, auth_client, app):
        from app.models import Study, User
        from datetime import datetime

        with app.app_context():
            user = User.query.filter_by(email='admin@example.com').first()
            s = Study(name='Also Delete', status=0, result_count=10,
                      created_at=datetime.now(), live_link_mode=True, visible=True)
            s.users.append(user)
            db.session.add(s)
            db.session.commit()
            sid = s.id
            db.session.delete(s)
            db.session.commit()

        r = auth_client.get(f'/study/{sid}')
        assert r.status_code == 404
