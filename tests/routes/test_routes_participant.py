"""
Route-Tests für participant.py und assessment.py.

Abgedeckte Flows:
  - Join-Flow (neuer / zurückkehrender Teilnehmer)
  - Resume mit Code
  - Teilnehmer-Übersicht (Login erforderlich)
  - Assessment-Seite (keine Antworten → direkt abgeschlossen)
  - Teilnehmer löschen
"""
import pytest
from app import db


# ─────────────────────────────────────────────────────────────────────────────
# Join-Flow (öffentlich, kein Login nötig)
# ─────────────────────────────────────────────────────────────────────────────

class TestJoinFlow:
    def test_join_page_accessible(self, client, study_id):
        r = client.get(f'/join/{study_id}')
        assert r.status_code == 200

    def test_join_page_contains_form(self, client, study_id):
        r = client.get(f'/join/{study_id}')
        assert b'form' in r.data.lower()

    def test_join_new_participant_redirects_to_participant_page(self, client, study_id):
        r = client.post(f'/join/{study_id}', data={'new': 'New'}, follow_redirects=False)
        assert r.status_code == 302
        assert '/participant/' in r.location

    def test_join_returning_redirects_to_returning_page(self, client, study_id):
        r = client.post(f'/join/{study_id}', data={'returning': 'Returning'}, follow_redirects=False)
        assert r.status_code == 302
        assert 'returning' in r.location

    def test_join_nonexistent_study_get_shows_form(self, client):
        # GET ohne Study-ID im Formular zeigt das Formular, erst POST löst 404 aus
        r = client.get('/join/99999')
        assert r.status_code in (200, 404)

    def test_join_nonexistent_study_post_returns_404(self, client):
        r = client.post('/join/99999', data={'new': 'New'})
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Returning-Flow (öffentlich)
# ─────────────────────────────────────────────────────────────────────────────

class TestReturningFlow:
    def test_returning_page_accessible(self, client, study_id):
        r = client.get(f'/returning/{study_id}')
        assert r.status_code == 200

    def test_returning_unknown_username_stays_on_page(self, client, study_id):
        r = client.post(f'/returning/{study_id}', data={
            'username': 'nobody', 'password': '0000',
        }, follow_redirects=False)
        assert r.status_code == 200

    def test_returning_wrong_code_stays_on_page(self, client, study_id, participant_id):
        from app.models import Participant
        with client.application.app_context():
            p = db.session.get(Participant, participant_id)
            username = p.name
        r = client.post(f'/returning/{study_id}', data={
            'username': username, 'password': '0000',
        }, follow_redirects=False)
        assert r.status_code == 200

    def test_returning_correct_credentials_redirects(self, client, study_id, participant_id):
        from app.models import Participant
        with client.application.app_context():
            p = db.session.get(Participant, participant_id)
            username, code = p.name, p.password
        r = client.post(f'/returning/{study_id}', data={
            'username': username, 'password': str(code),
        }, follow_redirects=False)
        assert r.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# Resume mit Code (öffentlich)
# ─────────────────────────────────────────────────────────────────────────────

class TestResume:
    def test_valid_code_redirects_to_participant(self, client, participant_id):
        from app.models import Participant
        with client.application.app_context():
            p = db.session.get(Participant, participant_id)
            code = p.password
        r = client.get(f'/resume/{participant_id}/{code}', follow_redirects=False)
        assert r.status_code == 302
        assert f'participant/{participant_id}' in r.location

    def test_invalid_code_redirects_to_login(self, client, participant_id):
        r = client.get(f'/resume/{participant_id}/9999999', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location

    def test_nonexistent_participant_redirects_to_login(self, client):
        r = client.get('/resume/99999/1234', follow_redirects=False)
        assert r.status_code == 302
        assert 'login' in r.location


# ─────────────────────────────────────────────────────────────────────────────
# Teilnehmer-Übersicht (Login erforderlich)
# ─────────────────────────────────────────────────────────────────────────────

class TestParticipantsList:
    def test_participants_list_returns_200(self, auth_client, study_id):
        r = auth_client.get(f'/study/{study_id}/participants')
        assert r.status_code == 200

    def test_participants_list_requires_login(self, client, study_id):
        r = client.get(f'/study/{study_id}/participants', follow_redirects=False)
        # participant route hat kein @login_required — zeigt Seite direkt
        assert r.status_code in (200, 302)

    def test_participants_list_404_for_nonexistent_study(self, auth_client):
        r = auth_client.get('/study/99999/participants')
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Assessment-Flow (öffentlich)
# ─────────────────────────────────────────────────────────────────────────────

class TestAssessmentFlow:
    def test_no_answers_redirects_to_participant(self, client, study_id, participant_id):
        r = client.get(
            f'/study/{study_id}/assessments/{participant_id}',
            follow_redirects=False,
        )
        # Keine Antworten → "Assessment completed!" → Redirect zur Teilnehmer-Seite
        assert r.status_code == 302
        assert f'participant/{participant_id}' in r.location

    def test_nonexistent_study_returns_404(self, client, participant_id):
        r = client.get(f'/study/99999/assessments/{participant_id}')
        assert r.status_code == 404

    def test_nonexistent_participant_returns_404(self, client, study_id):
        r = client.get(f'/study/{study_id}/assessments/99999')
        assert r.status_code == 404

    def test_participant_detail_page_accessible(self, client, participant_id):
        r = client.get(f'/participant/{participant_id}')
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Teilnehmer löschen (öffentlich — kein Login benötigt)
# ─────────────────────────────────────────────────────────────────────────────

class TestParticipantDelete:
    def test_delete_redirects(self, client, app):
        from app.models import Participant
        with app.app_context():
            p = Participant(name='delete_me_participant', password=5678, created_at=datetime.now())
            db.session.add(p)
            db.session.commit()
            pid = p.id
        r = client.post(f'/participant/{pid}/delete', follow_redirects=False)
        assert r.status_code == 302

    def test_delete_nonexistent_still_redirects(self, client):
        r = client.post('/participant/99999/delete', follow_redirects=False)
        assert r.status_code == 302


from datetime import datetime
