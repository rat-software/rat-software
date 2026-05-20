"""
Tests für helpers.clean_filter_string – URL-Normalisierung für Filterstrings.
Wurde aus assessment.py und participant.py nach helpers.py ausgelagert.
"""

import importlib.util
import os
import sys
import types
import pytest
from unittest.mock import MagicMock

# ── Mock Flask/DB/Crontab so helpers.py loads without a running app ──
_pkg = types.ModuleType('app')
_pkg.app = MagicMock()
_pkg.db = MagicMock()
_pkg.__path__ = []
sys.modules.setdefault('app', _pkg)

_forms = types.ModuleType('app.forms')
_forms.AnswerForm = type('AnswerForm', (), {})
sys.modules.setdefault('app.forms', _forms)

if 'app.models' not in sys.modules:
    sys.modules['app.models'] = types.ModuleType('app.models')
_models = sys.modules['app.models']
for _n in ('Option', 'Question'):
    if not hasattr(_models, _n):
        setattr(_models, _n, type(_n, (), {}))

_crontab = types.ModuleType('crontab')
_crontab.CronTab = type('CronTab', (), {})
sys.modules.setdefault('crontab', _crontab)


_HELPERS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-frontend', 'app', 'helpers.py',
)
_spec = importlib.util.spec_from_file_location('app.helpers', _HELPERS_PATH)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = 'app'
sys.modules['app.helpers'] = _mod
_spec.loader.exec_module(_mod)

clean_filter_string = _mod.clean_filter_string


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCleanFilterStringScheme:
    def test_full_https_url_returns_domain(self):
        assert clean_filter_string("https://example.com/path") == "example.com"

    def test_full_http_url_returns_domain(self):
        assert clean_filter_string("http://example.com/") == "example.com"

    def test_no_scheme_gets_prepended(self):
        assert clean_filter_string("example.com") == "example.com"

    def test_no_scheme_with_path(self):
        assert clean_filter_string("example.com/some/path") == "example.com"


class TestCleanFilterStringWww:
    def test_strips_www_prefix(self):
        assert clean_filter_string("https://www.example.com") == "example.com"

    def test_strips_www_without_scheme(self):
        assert clean_filter_string("www.example.com") == "example.com"

    def test_no_www_stays_unchanged(self):
        assert clean_filter_string("blog.example.com") == "blog.example.com"

    def test_wwwX_prefix_not_stripped(self):
        # "www2.example.com" darf nicht abgeschnitten werden
        assert clean_filter_string("www2.example.com") == "www2.example.com"


class TestCleanFilterStringCase:
    def test_uppercase_domain_lowercased(self):
        assert clean_filter_string("https://EXAMPLE.COM") == "example.com"

    def test_mixed_case_lowercased(self):
        assert clean_filter_string("https://Example.Com/Path") == "example.com"

    def test_bare_uppercase_no_scheme(self):
        assert clean_filter_string("EXAMPLE.COM") == "example.com"


class TestCleanFilterStringEdgeCases:
    def test_domain_with_port(self):
        assert clean_filter_string("https://example.com:8080") == "example.com:8080"

    def test_subdomain_preserved(self):
        assert clean_filter_string("https://sub.example.com") == "sub.example.com"

    def test_empty_string_fallback(self):
        # Leerer String: urlparse liefert leeres netloc → Fallback auf .lower()
        result = clean_filter_string("")
        assert isinstance(result, str)

    def test_plain_string_no_dot(self):
        # Kein Dot: wird als Pfad interpretiert, netloc bleibt leer
        result = clean_filter_string("justsometext")
        assert isinstance(result, str)
