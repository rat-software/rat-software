"""
Route-Tests für questions.py, query.py, url_filters.py, export.py, analysis.py.

Abgedeckte Routen:
  - Fragen: erstellen (GET), löschen (GET/POST), JSON-Export
  - Queries: hinzufügen, löschen, Extension-Sperre
  - URL-Filter: lesen, speichern
  - Export: Formular-Seite, Excel-Download
  - Analyse: Analyse-Seite, Export-Redirect
"""
import pytest
from app import db


# ─────────────────────────────────────────────────────────────────────────────
# Fragen (questions.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestQuestionRoutes:
    def test_new_question_form_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/question/new')
        assert r.status_code == 200

    def test_new_question_form_contains_input(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/question/new')
        assert b'input' in r.data.lower() or b'textarea' in r.data.lower()

    def test_new_question_requires_login(self, client, study_id):
        r = client.get(f'/study/{study_id}/question/new', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_delete_question_get_shows_confirmation(self, auth_client, question_id):
        r = auth_client.get(f'/question/{question_id}/delete')
        assert r.status_code == 200

    def test_delete_question_post_redirects_to_questions(self, auth_client, question_id, study_id):
        r = auth_client.post(
            f'/question/{question_id}/delete',
            data={'submit': 'Confirm'},
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert f'study/{study_id}/questions' in r.location

    def test_delete_nonexistent_question_returns_404(self, auth_client):
        r = auth_client.get('/question/99999/delete')
        assert r.status_code == 404

    def test_export_questions_json_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/questions/export')
        assert r.status_code == 200

    def test_export_questions_requires_login(self, client, study_id):
        r = client.get(f'/study/{study_id}/questions/export', follow_redirects=False)
        assert r.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# Queries (query.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryRoutes:
    def test_add_queries_redirects_to_study(self, auth_client, study_id):
        r = auth_client.post(f'/study/{study_id}/add_queries', data={
            'new_keywords': 'seo tools\nkeyword research',
            'query_limit':  '10',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert f'study/{study_id}' in r.location

    def test_add_queries_empty_still_redirects(self, auth_client, study_id):
        r = auth_client.post(f'/study/{study_id}/add_queries', data={
            'new_keywords': '',
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_add_queries_requires_login(self, client, study_id):
        r = client.post(f'/study/{study_id}/add_queries', data={
            'new_keywords': 'test',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_delete_query_redirects(self, auth_client, query_id, study_id):
        r = auth_client.post(f'/query/{query_id}/delete', follow_redirects=False)
        assert r.status_code == 302
        assert f'study/{study_id}' in r.location

    def test_deleted_query_is_gone(self, auth_client, app, study_id):
        from app.models import Query
        with app.app_context():
            q = Query(query='to_delete_kw', study_id=study_id, limit=5, source_type='manual')
            db.session.add(q)
            db.session.commit()
            qid = q.id
        auth_client.post(f'/query/{qid}/delete')
        with app.app_context():
            assert db.session.get(Query, qid) is None

    def test_extension_query_cannot_be_deleted(self, auth_client, app, study_id):
        from app.models import Query
        with app.app_context():
            q = Query(query='ext kw', study_id=study_id, limit=10, source_type='extension')
            db.session.add(q)
            db.session.commit()
            qid = q.id
        r = auth_client.post(f'/query/{qid}/delete', follow_redirects=True)
        assert r.status_code == 200
        assert b'extension' in r.data.lower()
        with app.app_context():
            assert db.session.get(Query, qid) is not None
            db.session.delete(db.session.get(Query, qid))
            db.session.commit()

    def test_delete_nonexistent_query_returns_404(self, auth_client):
        r = auth_client.post('/query/99999/delete')
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# URL-Filter (url_filters.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestUrlFilterRoutes:
    def test_filters_page_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/filters')
        assert r.status_code == 200

    def test_filters_requires_login(self, client, study_id):
        r = client.get(f'/study/{study_id}/filters', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_filters_post_saves_and_redirects(self, auth_client, study_id):
        r = auth_client.post(f'/study/{study_id}/filters', data={
            'include_urls': 'example.com\nwikipedia.org',
            'exclude_urls': 'spam.com',
            'submit': 'Confirm',
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_filters_post_persists_include(self, auth_client, app, study_id):
        auth_client.post(f'/study/{study_id}/filters', data={
            'include_urls': 'persistent-include.com',
            'exclude_urls': '',
            'submit': 'Confirm',
        })
        r = auth_client.get(f'/study/{study_id}/filters')
        assert b'persistent-include.com' in r.data

    def test_filters_post_persists_exclude(self, auth_client, app, study_id):
        auth_client.post(f'/study/{study_id}/filters', data={
            'include_urls': '',
            'exclude_urls': 'block-this.com',
            'submit': 'Confirm',
        })
        r = auth_client.get(f'/study/{study_id}/filters')
        assert b'block-this.com' in r.data

    def test_filters_post_clears_old_filters(self, auth_client, study_id):
        auth_client.post(f'/study/{study_id}/filters', data={
            'include_urls': 'first.com', 'exclude_urls': '', 'submit': 'Confirm',
        })
        auth_client.post(f'/study/{study_id}/filters', data={
            'include_urls': 'second.com', 'exclude_urls': '', 'submit': 'Confirm',
        })
        r = auth_client.get(f'/study/{study_id}/filters')
        assert b'first.com' not in r.data
        assert b'second.com' in r.data


# ─────────────────────────────────────────────────────────────────────────────
# Export (export.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestExportRoutes:
    def test_export_page_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/{study_id}/export')
        assert r.status_code == 200

    def test_export_requires_login(self, client, study_id):
        r = client.get(f'/{study_id}/export', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_export_404_for_nonexistent_study(self, auth_client):
        r = auth_client.get('/99999/export')
        assert r.status_code == 404

    def test_export_post_returns_excel_file(self, auth_client, study_id, question_id):
        # question_id stellt sicher, dass mindestens ein Sheet ins Workbook geschrieben wird
        r = auth_client.post(f'/{study_id}/export', data={})
        assert r.status_code == 200
        ct = r.content_type
        assert any(x in ct for x in ('spreadsheet', 'excel', 'octet-stream'))

    def test_export_post_filename_contains_study_id(self, auth_client, study_id, question_id):
        r = auth_client.post(f'/{study_id}/export', data={})
        cd = r.headers.get('Content-Disposition', '')
        assert str(study_id) in cd


# ─────────────────────────────────────────────────────────────────────────────
# Analyse (analysis.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalysisRoutes:
    def test_analysis_page_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/{study_id}/analysis')
        assert r.status_code == 200

    def test_analysis_requires_login(self, client, study_id):
        r = client.get(f'/{study_id}/analysis', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_analysis_404_for_nonexistent_study(self, auth_client):
        r = auth_client.get('/99999/analysis')
        assert r.status_code == 404

    def test_export_analysis_redirects_to_export(self, auth_client, study_id):
        r = auth_client.get(f'/{study_id}/export-analysis', follow_redirects=False)
        assert r.status_code == 302
        assert 'export' in r.location
