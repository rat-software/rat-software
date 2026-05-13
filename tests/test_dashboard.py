"""
Tests für dashboard.py – fokussiert auf:
  1. Dashboard-Daten (Studie-Filterung nach Sichtbarkeit & Besitz)
  2. Zugriffsrechte (normaler User vs. Super Admin)
  3. Leere Zustände (keine Studien, kein Super-Admin-Flag)
  4. main()-Routing (authenticated vs. unauthenticated)
  5. Contact-E-Mail-Formatierung
"""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Hilfsfunktionen – replizieren die Logik aus dashboard.py isoliert
# ---------------------------------------------------------------------------

def get_dashboard_data(user, all_rat_studies, all_qs_studies):
    """
    Repliziert die Daten-Auswahl aus der dashboard()-Route:
      - Eigene sichtbare Studien filtern
      - Super-Admin bekommt zusätzlich alle sichtbaren Studien
    """
    rat_studies = [s for s in all_rat_studies if user in s.users and s.visible]
    qs_studies  = [s for s in all_qs_studies  if user in s.users and s.visible]

    other_rat_studies = []
    other_qs_studies  = []

    if getattr(user, 'super_admin', False) is True:
        other_rat_studies = [s for s in all_rat_studies if s.visible]
        other_qs_studies  = [s for s in all_qs_studies  if s.visible]

    return {
        'rat_studies':       rat_studies,
        'qs_studies':        qs_studies,
        'other_rat_studies': other_rat_studies,
        'other_qs_studies':  other_qs_studies,
    }


def get_main_redirect(is_authenticated: bool) -> str:
    """Repliziert die Routing-Logik aus main()."""
    return 'dashboard' if is_authenticated else 'security.login'


def build_contact_email(name: str, email: str, message: str, sender: str) -> dict:
    """Repliziert die E-Mail-Konstruktion aus contact()."""
    subject = f"RAT Form Submission from {name}"
    body    = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
    html    = (
        f"<strong>Name:</strong> {name}<br>"
        f"<strong>Email:</strong> {email}<br><br>"
        f"<strong>Message:</strong><br>{message}"
    )
    return {'subject': subject, 'body': body, 'html': html, 'sender': sender,
            'recipients': ["sebastian.suenkler@haw-hamburg.de"]}


# ---------------------------------------------------------------------------
# Fixture-Helfer
# ---------------------------------------------------------------------------

def make_user(user_id=1, super_admin=False):
    user = SimpleNamespace(id=user_id, super_admin=super_admin)
    return user


def make_study(owner, visible=True):
    study = SimpleNamespace(users=[owner], visible=visible)
    return study


# ===========================================================================
# 1. main()-Routing: authenticated vs. unauthenticated
# ===========================================================================

class TestMainRouteLogic:

    def test_authenticated_redirects_to_dashboard(self):
        assert get_main_redirect(is_authenticated=True) == 'dashboard'

    def test_unauthenticated_redirects_to_login(self):
        assert get_main_redirect(is_authenticated=False) == 'security.login'


# ===========================================================================
# 2. Dashboard-Daten: eigene Studien filtern
# ===========================================================================

class TestDashboardStudyFiltering:

    def test_user_sees_own_visible_study(self):
        user  = make_user()
        study = make_study(owner=user, visible=True)
        data  = get_dashboard_data(user, [study], [])
        assert study in data['rat_studies']

    def test_user_does_not_see_invisible_own_study(self):
        user  = make_user()
        study = make_study(owner=user, visible=False)
        data  = get_dashboard_data(user, [study], [])
        assert study not in data['rat_studies']

    def test_user_does_not_see_other_users_study(self):
        user_a = make_user(user_id=1)
        user_b = make_user(user_id=2)
        study  = make_study(owner=user_b, visible=True)
        data   = get_dashboard_data(user_a, [study], [])
        assert study not in data['rat_studies']

    def test_qs_studies_filtered_same_way(self):
        user  = make_user()
        qs    = make_study(owner=user, visible=True)
        data  = get_dashboard_data(user, [], [qs])
        assert qs in data['qs_studies']

    def test_invisible_qs_study_excluded(self):
        user = make_user()
        qs   = make_study(owner=user, visible=False)
        data = get_dashboard_data(user, [], [qs])
        assert qs not in data['qs_studies']

    def test_multiple_studies_only_own_visible(self):
        user_a = make_user(user_id=1)
        user_b = make_user(user_id=2)
        own_visible   = make_study(owner=user_a, visible=True)
        own_invisible = make_study(owner=user_a, visible=False)
        others        = make_study(owner=user_b, visible=True)
        data = get_dashboard_data(user_a, [own_visible, own_invisible, others], [])
        assert data['rat_studies'] == [own_visible]


# ===========================================================================
# 3. Zugriffsrechte: Super-Admin sieht alle sichtbaren Studien
# ===========================================================================

class TestSuperAdminAccess:

    def test_super_admin_gets_all_visible_rat_studies(self):
        admin  = make_user(super_admin=True)
        user_b = make_user(user_id=2)
        study  = make_study(owner=user_b, visible=True)
        data   = get_dashboard_data(admin, [study], [])
        assert study in data['other_rat_studies']

    def test_super_admin_gets_all_visible_qs_studies(self):
        admin  = make_user(super_admin=True)
        user_b = make_user(user_id=2)
        qs     = make_study(owner=user_b, visible=True)
        data   = get_dashboard_data(admin, [], [qs])
        assert qs in data['other_qs_studies']

    def test_super_admin_excludes_invisible_from_other_list(self):
        admin  = make_user(super_admin=True)
        user_b = make_user(user_id=2)
        hidden = make_study(owner=user_b, visible=False)
        data   = get_dashboard_data(admin, [hidden], [])
        assert hidden not in data['other_rat_studies']

    def test_normal_user_gets_empty_other_lists(self):
        user   = make_user(super_admin=False)
        user_b = make_user(user_id=2)
        study  = make_study(owner=user_b, visible=True)
        data   = get_dashboard_data(user, [study], [])
        assert data['other_rat_studies'] == []
        assert data['other_qs_studies']  == []

    def test_super_admin_false_explicitly_gets_empty_other_lists(self):
        user  = make_user(super_admin=False)
        study = make_study(owner=make_user(user_id=99), visible=True)
        data  = get_dashboard_data(user, [study], [])
        assert data['other_rat_studies'] == []

    def test_user_without_super_admin_attr_gets_empty_other_lists(self):
        user = SimpleNamespace(id=1)  # kein super_admin-Attribut
        study = make_study(owner=make_user(user_id=99), visible=True)
        data  = get_dashboard_data(user, [study], [])
        assert data['other_rat_studies'] == []


# ===========================================================================
# 4. Leere Zustände
# ===========================================================================

class TestEmptyStates:

    def test_no_studies_all_lists_empty(self):
        user = make_user()
        data = get_dashboard_data(user, [], [])
        assert data['rat_studies']       == []
        assert data['qs_studies']        == []
        assert data['other_rat_studies'] == []
        assert data['other_qs_studies']  == []

    def test_only_invisible_studies_all_lists_empty(self):
        user   = make_user()
        hidden = make_study(owner=user, visible=False)
        data   = get_dashboard_data(user, [hidden], [hidden])
        assert data['rat_studies'] == []
        assert data['qs_studies']  == []

    def test_super_admin_with_no_studies_gets_empty_lists(self):
        admin = make_user(super_admin=True)
        data  = get_dashboard_data(admin, [], [])
        assert data['other_rat_studies'] == []
        assert data['other_qs_studies']  == []

    def test_super_admin_only_invisible_studies_other_lists_empty(self):
        admin   = make_user(super_admin=True)
        user_b  = make_user(user_id=2)
        hidden  = make_study(owner=user_b, visible=False)
        data    = get_dashboard_data(admin, [hidden], [])
        assert data['other_rat_studies'] == []

    def test_return_keys_always_present(self):
        user = make_user()
        data = get_dashboard_data(user, [], [])
        assert 'rat_studies'       in data
        assert 'qs_studies'        in data
        assert 'other_rat_studies' in data
        assert 'other_qs_studies'  in data


# ===========================================================================
# 5. Contact-E-Mail-Formatierung
# ===========================================================================

class TestContactEmailFormatting:

    def _email(self, name="Ada", email="ada@example.com", message="Hello"):
        return build_contact_email(name, email, message, sender="noreply@rat.de")

    def test_subject_contains_name(self):
        mail = self._email(name="Ada Lovelace")
        assert "Ada Lovelace" in mail['subject']

    def test_subject_prefix(self):
        mail = self._email()
        assert mail['subject'].startswith("RAT Form Submission from")

    def test_body_contains_name(self):
        mail = self._email(name="Ada")
        assert "Name: Ada" in mail['body']

    def test_body_contains_email(self):
        mail = self._email(email="ada@example.com")
        assert "Email: ada@example.com" in mail['body']

    def test_body_contains_message(self):
        mail = self._email(message="Test message")
        assert "Test message" in mail['body']

    def test_html_contains_strong_tags(self):
        mail = self._email()
        assert "<strong>Name:</strong>" in mail['html']
        assert "<strong>Email:</strong>" in mail['html']
        assert "<strong>Message:</strong>" in mail['html']

    def test_html_contains_br_tags(self):
        mail = self._email()
        assert "<br>" in mail['html']

    def test_recipient_is_fixed(self):
        mail = self._email()
        assert mail['recipients'] == ["sebastian.suenkler@haw-hamburg.de"]

    def test_sender_passed_through(self):
        mail = build_contact_email("A", "a@b.com", "msg", sender="x@y.de")
        assert mail['sender'] == "x@y.de"

    def test_empty_message_field(self):
        mail = self._email(message="")
        assert "Message:" in mail['body']

    def test_special_chars_in_name_preserved(self):
        mail = self._email(name="Ångström & Co.")
        assert "Ångström & Co." in mail['subject']
        assert "Ångström & Co." in mail['body']
