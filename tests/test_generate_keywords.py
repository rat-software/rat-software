"""
Unit tests for rat-backend/query_sampler/generate_keywords.py

The file is a script: all logic runs at module level on import.
Strategy:
  - Load the module via importlib with fully mocked `db` and `google.ads` stubs.
  - Load once per scenario (empty keywords / status-0 only / status-2 triggers
    the inner if-block that defines `main` and `map_locations_ids_to_resource_names`).
  - Test the two inner functions (main, map_locations_ids_to_resource_names) by
    calling them on the loaded module after the appropriate setup.
"""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, call, patch

# ── Path ──────────────────────────────────────────────────────────────────────
_GK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'query_sampler', 'generate_keywords.py',
)

# ── Stub google.ads (once, before any import) ─────────────────────────────────
for _name in [
    'google', 'google.ads', 'google.ads.googleads',
    'google.ads.googleads.client', 'google.ads.googleads.errors',
]:
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        _m.__path__ = []
        sys.modules[_name] = _m

sys.modules['google.ads.googleads.client'].GoogleAdsClient = MagicMock()


class _FakeGoogleAdsException(Exception):
    request_id = 'fake-req'
    error      = MagicMock()
    failure    = MagicMock()
    failure.errors = []


sys.modules['google.ads.googleads.errors'].GoogleAdsException = _FakeGoogleAdsException


# ── Helpers ───────────────────────────────────────────────────────────────────

_DB_FUNCTIONS = [
    'get_keywords_bg', 'get_keyword_status', 'update_keyword_status',
    'insert_keyword_idea', 'get_studies', 'insert_study', 'get_study',
    'get_regions', 'get_languages', 'get_keywords', 'get_keyword_ideas',
    'insert_keyword', 'check_keyword', 'get_keyword_status_study',
    'select_keywords_ideas', 'reset_hanging_qs_jobs',
]


def _make_db_stub(keywords=None, status_0=None, status_2=None):
    """Build a db stub module.

    status_0 / status_2: return values of get_keyword_status for those statuses.
    """
    db = types.ModuleType('db')
    db.get_keywords_bg = MagicMock(return_value=keywords or [])

    def _status_side_effect(keyword_id, status):
        if status == 0:
            return status_0
        if status == 2:
            return status_2
        return None

    db.get_keyword_status      = MagicMock(side_effect=_status_side_effect)
    db.update_keyword_status   = MagicMock()
    db.insert_keyword_idea     = MagicMock()
    for fn in _DB_FUNCTIONS[4:]:          # remaining functions – unused in tests
        setattr(db, fn, MagicMock())
    return db


def _make_keyword(study_id=1, keyword_id=10, keyword='berlin',
                  region_criterion_id='2276', language_criterion_id='1001'):
    return {
        'study_id':              study_id,
        'keyword_id':            keyword_id,
        'keyword':               keyword,
        'region_criterion_id':   region_criterion_id,
        'language_criterion_id': language_criterion_id,
    }


def _load(db_stub):
    """Execute generate_keywords.py with the given db stub; return the module."""
    sys.modules['db'] = db_stub
    spec = importlib.util.spec_from_file_location('generate_keywords_fresh', _GK_PATH)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_client(ideas=None):
    """Build a minimal GoogleAds client mock."""
    client = MagicMock()
    idea_service = client.get_service.return_value
    idea_service.generate_keyword_ideas.return_value = ideas or []
    return client


def _make_idea(text='berlin trip', avg_monthly_searches=5000, competition='LOW'):
    idea = MagicMock()
    idea.text = text
    idea.keyword_idea_metrics.competition.name        = competition
    idea.keyword_idea_metrics.avg_monthly_searches    = avg_monthly_searches
    return idea


# ═════════════════════════════════════════════════════════════════════════════
# Module-level flow — no keywords
# ═════════════════════════════════════════════════════════════════════════════

class TestFlowNoKeywords(unittest.TestCase):
    """When get_keywords_bg returns [], the loops never run."""

    @classmethod
    def setUpClass(cls):
        cls.db  = _make_db_stub(keywords=[])
        cls.mod = _load(cls.db)

    def test_get_keywords_bg_is_called(self):
        self.db.get_keywords_bg.assert_called_once()

    def test_keywords_attribute_is_empty(self):
        self.assertEqual(self.mod.keywords, [])

    def test_no_status_check_performed(self):
        self.db.get_keyword_status.assert_not_called()

    def test_no_status_update_performed(self):
        self.db.update_keyword_status.assert_not_called()

    def test_main_not_defined_on_module(self):
        self.assertFalse(hasattr(self.mod, 'main'))

    def test_map_fn_not_defined_on_module(self):
        self.assertFalse(hasattr(self.mod, 'map_locations_ids_to_resource_names'))


# ═════════════════════════════════════════════════════════════════════════════
# Module-level flow — first loop (status 0 → mark as 2)
# ═════════════════════════════════════════════════════════════════════════════

class TestFlowFirstLoop(unittest.TestCase):
    """First loop marks keywords with status=0 as processing (status=2)."""

    @classmethod
    def setUpClass(cls):
        cls.kw  = _make_keyword(keyword_id=10)
        # status=0 found, status=2 NOT found (so second loop does nothing)
        cls.db  = _make_db_stub(keywords=[cls.kw], status_0={'id': 10}, status_2=None)
        cls.mod = _load(cls.db)

    def test_update_keyword_status_called_with_2(self):
        statuses = [c[0][0] for c in self.db.update_keyword_status.call_args_list]
        self.assertIn(2, statuses)

    def test_update_keyword_status_called_with_correct_id(self):
        ids = [c[0][1] for c in self.db.update_keyword_status.call_args_list]
        self.assertIn(10, ids)

    def test_no_status_update_when_status_0_not_found(self):
        kw  = _make_keyword(keyword_id=99)
        db  = _make_db_stub(keywords=[kw], status_0=None, status_2=None)
        _load(db)
        db.update_keyword_status.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# Module-level flow — second loop defines inner functions
# ═════════════════════════════════════════════════════════════════════════════

class TestFlowSecondLoop(unittest.TestCase):
    """When status=2 is found, main() and map_fn() are defined on the module."""

    @classmethod
    def setUpClass(cls):
        cls.kw  = _make_keyword(keyword_id=10)
        cls.db  = _make_db_stub(keywords=[cls.kw], status_0={'id': 10}, status_2={'id': 10})
        cls.mod = _load(cls.db)

    def test_main_is_defined(self):
        self.assertTrue(hasattr(self.mod, 'main'))
        self.assertTrue(callable(self.mod.main))

    def test_map_fn_is_defined(self):
        self.assertTrue(hasattr(self.mod, 'map_locations_ids_to_resource_names'))
        self.assertTrue(callable(self.mod.map_locations_ids_to_resource_names))

    def test_module_study_id_set(self):
        self.assertEqual(self.mod.study_id, 1)

    def test_module_keyword_id_set(self):
        self.assertEqual(self.mod.keyword_id, 10)

    def test_multiple_keywords_all_checked(self):
        kw1 = _make_keyword(keyword_id=1)
        kw2 = _make_keyword(keyword_id=2)
        db  = _make_db_stub(keywords=[kw1, kw2], status_0={'id': 1}, status_2=None)
        _load(db)
        checked_ids = [c[0][0] for c in db.get_keyword_status.call_args_list
                       if c[0][1] == 0]
        self.assertIn(1, checked_ids)
        self.assertIn(2, checked_ids)


# ═════════════════════════════════════════════════════════════════════════════
# map_locations_ids_to_resource_names
# ═════════════════════════════════════════════════════════════════════════════

class TestMapLocationsIdsToResourceNames(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        kw      = _make_keyword()
        db      = _make_db_stub(keywords=[kw], status_0={'id': 10}, status_2={'id': 10})
        cls.mod = _load(db)
        # Store as staticmethod to prevent Python's descriptor protocol from
        # injecting `self` as the first argument when called via an instance.
        cls.fn  = staticmethod(cls.mod.map_locations_ids_to_resource_names)

    def _make_geo_client(self):
        client = MagicMock()
        client.get_service.return_value.geo_target_constant_path.side_effect = (
            lambda loc_id: f'geoTargets/{loc_id}'
        )
        return client

    def test_returns_list(self):
        client = self._make_geo_client()
        result = self.fn(client, ['2276', '1003854'])
        self.assertIsInstance(result, list)

    def test_length_matches_input(self):
        client = self._make_geo_client()
        result = self.fn(client, ['2276', '1003854', '9999'])
        self.assertEqual(len(result), 3)

    def test_calls_geo_target_constant_path_for_each_id(self):
        client = self._make_geo_client()
        self.fn(client, ['2276', '1003854'])
        geo_service = client.get_service.return_value
        calls = [c[0][0] for c in geo_service.geo_target_constant_path.call_args_list]
        self.assertIn('2276',    calls)
        self.assertIn('1003854', calls)

    def test_resource_names_in_output(self):
        client = self._make_geo_client()
        result = self.fn(client, ['2276'])
        self.assertIn('geoTargets/2276', result)

    def test_empty_list_returns_empty(self):
        client = self._make_geo_client()
        result = self.fn(client, [])
        self.assertEqual(result, [])


# ═════════════════════════════════════════════════════════════════════════════
# main() — seed selection
# ═════════════════════════════════════════════════════════════════════════════

class TestMainSeedSelection(unittest.TestCase):
    """main() chooses url_seed / keyword_seed / keyword_and_url_seed correctly."""

    @classmethod
    def setUpClass(cls):
        kw     = _make_keyword()
        db     = _make_db_stub(keywords=[kw], status_0={'id': 10}, status_2={'id': 10})
        cls.mod = _load(db)

    def _call_main(self, keyword_texts, page_url, ideas=None):
        client  = _make_client(ideas or [])
        request = MagicMock()
        client.get_type.return_value = request
        self.mod.main(client, 'cid-123', ['2276'], '1001', keyword_texts, page_url)
        return request

    def test_raises_value_error_when_neither_keywords_nor_url(self):
        client = _make_client()
        with self.assertRaises(ValueError):
            self.mod.main(client, 'cid-123', ['2276'], '1001', [], '')

    def test_uses_keyword_seed_when_only_keywords(self):
        req = self._call_main(['berlin'], '')
        req.keyword_seed.keywords.extend.assert_called_once_with(['berlin'])

    def test_uses_url_seed_when_only_page_url(self):
        req = self._call_main([], 'https://example.com')
        self.assertEqual(req.url_seed.url, 'https://example.com')

    def test_does_not_extend_keywords_when_only_url(self):
        req = self._call_main([], 'https://example.com')
        req.keyword_seed.keywords.extend.assert_not_called()

    def test_uses_keyword_and_url_seed_when_both(self):
        req = self._call_main(['berlin'], 'https://example.com')
        self.assertEqual(req.keyword_and_url_seed.url, 'https://example.com')
        req.keyword_and_url_seed.keywords.extend.assert_called_once_with(['berlin'])

    def test_include_adult_keywords_set_to_false(self):
        req = self._call_main(['berlin'], '')
        self.assertFalse(req.include_adult_keywords)

    def test_customer_id_set_on_request(self):
        req = self._call_main(['berlin'], '')
        self.assertEqual(req.customer_id, 'cid-123')


# ═════════════════════════════════════════════════════════════════════════════
# main() — idea insertion
# ═════════════════════════════════════════════════════════════════════════════

class TestMainIdeaInsertion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        kw      = _make_keyword(study_id=1, keyword_id=10)
        cls.db  = _make_db_stub(keywords=[kw], status_0={'id': 10}, status_2={'id': 10})
        cls.mod = _load(cls.db)

    def test_insert_keyword_idea_called_for_each_idea(self):
        ideas  = [_make_idea('idea A', 1000, 'LOW'), _make_idea('idea B', 2000, 'HIGH')]
        client = _make_client(ideas)
        client.get_type.return_value = MagicMock()

        self.mod.insert_keyword_idea = MagicMock()
        self.mod.main(client, 'cid', ['2276'], '1001', ['berlin'], '')

        self.assertEqual(self.mod.insert_keyword_idea.call_count, 2)

    def test_insert_keyword_idea_receives_correct_text(self):
        ideas  = [_make_idea('berlin trip', 5000, 'MEDIUM')]
        client = _make_client(ideas)
        client.get_type.return_value = MagicMock()

        self.mod.insert_keyword_idea = MagicMock()
        self.mod.main(client, 'cid', ['2276'], '1001', ['berlin'], '')

        args = self.mod.insert_keyword_idea.call_args[0]
        self.assertIn('berlin trip', args)

    def test_insert_keyword_idea_receives_avg_monthly_searches(self):
        ideas  = [_make_idea('x', 9999, 'LOW')]
        client = _make_client(ideas)
        client.get_type.return_value = MagicMock()

        self.mod.insert_keyword_idea = MagicMock()
        self.mod.main(client, 'cid', ['2276'], '1001', ['x'], '')

        args = self.mod.insert_keyword_idea.call_args[0]
        self.assertIn(9999, args)

    def test_no_insert_when_no_ideas_returned(self):
        client = _make_client([])
        client.get_type.return_value = MagicMock()

        self.mod.insert_keyword_idea = MagicMock()
        self.mod.main(client, 'cid', ['2276'], '1001', ['berlin'], '')

        self.mod.insert_keyword_idea.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# main() — status update after processing
# ═════════════════════════════════════════════════════════════════════════════

class TestMainStatusUpdate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        kw      = _make_keyword(keyword_id=10)
        cls.db  = _make_db_stub(keywords=[kw], status_0={'id': 10}, status_2={'id': 10})
        cls.mod = _load(cls.db)

    def _run_main(self):
        client = _make_client([])
        client.get_type.return_value = MagicMock()
        self.mod.update_keyword_status = MagicMock()
        self.mod.main(client, 'cid', ['2276'], '1001', ['berlin'], '')
        return self.mod.update_keyword_status

    def test_update_keyword_status_called_after_main(self):
        mock_update = self._run_main()
        mock_update.assert_called_once()

    def test_status_set_to_1_after_processing(self):
        mock_update = self._run_main()
        status_arg = mock_update.call_args[0][0]
        self.assertEqual(status_arg, 1)

    def test_correct_keyword_id_in_status_update(self):
        mock_update = self._run_main()
        keyword_id_arg = mock_update.call_args[0][1]
        self.assertEqual(keyword_id_arg, 10)


if __name__ == '__main__':
    unittest.main()
