"""
Trimmed unit tests for rat-backend/sources/sources_scraper.py

SourcesScraper.__init__  — stores all six attributes
SourcesScraper.scrape()  — key decision branches (no real threads / DB / browser):
  • check_progress=True            → source skipped entirely
  • duplicate source detected      → update_result_source called, no thread
  • source_id=False                → no scrape, no update_source
  • no proxy for foreign country   → progress=-1, update_source called, continue
  • success scrape                 → progress=1, update_source + update_result_source
  • status_code != 200             → progress=-1
  • content_type == 'error'        → progress=-1
  • 'timeout' in error_codes       → progress=-1
  • proxy_error appended to error_code
"""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ── Paths ──────────────────────────────────────────────────────────────────────
_SOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'sources',
)
_LIBS_DIR = os.path.join(_SOURCES_DIR, 'libs')

# ── libs stubs ─────────────────────────────────────────────────────────────────

_libs_pkg = types.ModuleType('libs')
_libs_pkg.__path__ = [_LIBS_DIR]
sys.modules.setdefault('libs', _libs_pkg)

for _sname, _attrs in [
    ('libs.lib_logger',        {'Logger':  type('Logger',  (), {})}),
    ('libs.lib_db',            {'DB':      type('DB',      (), {})}),
    ('libs.lib_helper',        {'Helper':  type('Helper',  (), {'file_to_dict': lambda self, p: {}})}),
    ('libs.lib_sources',       {'Sources': type('Sources', (), {})}),
    ('libs.lib_proxy_checker', {
        'check_proxy':          MagicMock(),
        'get_working_proxy':    MagicMock(),
        'get_proxy_for_scraping': MagicMock(return_value=(None, None)),
    }),
]:
    if _sname not in sys.modules:
        _m = types.ModuleType(_sname)
        for k, v in _attrs.items():
            setattr(_m, k, v)
        sys.modules[_sname] = _m
        setattr(_libs_pkg, _sname.split('.')[-1], _m)

# ── Load module ────────────────────────────────────────────────────────────────

sys.path.insert(0, _SOURCES_DIR)

_spec = importlib.util.spec_from_file_location(
    'sources_scraper',
    os.path.join(_SOURCES_DIR, 'sources_scraper.py'),
)
_mod = importlib.util.module_from_spec(_spec)
with patch('builtins.print'):
    _spec.loader.exec_module(_mod)
sys.modules['sources_scraper'] = _mod

from sources_scraper import SourcesScraper


# ── Fixtures ───────────────────────────────────────────────────────────────────

_URL     = 'http://example.com'
_GOOD_RESULT = {
    'file_path':    'file.zip',
    'request':      {'content_type': 'html', 'status_code': 200},
    'final_url':    'http://example.com/',
    'meta':         {'ip': '1.2.3.4', 'main': 'http://example.com/'},
    'error_codes':  '',
    'content_dict': {'': ''},
}


def _make_db(
    check_progress=False,
    source_id_check=None,
    source_id_by_result=True,
    result_source_source=42,
    counter=1,
):
    db = MagicMock()
    db.check_progress.return_value              = check_progress
    db.get_source_check.return_value            = source_id_check
    db.get_source_check_by_result_id.return_value = source_id_by_result
    db.get_result_source_source.return_value    = result_source_source
    db.get_source_counter_result.return_value   = counter
    db.get_result_content.return_value          = None
    return db


def _make_sources(save_result=None):
    s = MagicMock()
    s.get_result_meta.return_value = {'ip': '1.2.3.4', 'main': 'http://example.com/'}
    s.save_code.return_value       = save_result or _GOOD_RESULT
    return s


class _SyncExecutor:
    """Replaces ThreadPoolExecutor inside scrape_url — runs fn synchronously."""
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def submit(self, fn, *args, **kwargs):
        future = MagicMock()
        try:
            future.result.return_value = fn(*args, **kwargs)
        except Exception as e:
            future.result.side_effect = e
        return future


def _run(
    get_sources=None,
    save_result=None,
    db=None,
    proxy_return=(None, None),
    country_proxy=None,
    country='Germany',
    **db_kwargs,
):
    _db      = db or _make_db(**db_kwargs)
    _sources = _make_sources(save_result)
    _logger  = MagicMock()

    row = (1, _URL, country_proxy, 'DE')
    scraper = SourcesScraper(
        get_sources = get_sources if get_sources is not None else [row],
        job_server  = 'srv',
        db          = _db,
        logger      = _logger,
        sources     = _sources,
        country     = country,
    )

    # Patch the ThreadPoolExecutor used inside scrape_url so save_code runs
    # synchronously — patching threading.Thread would also break the internal
    # worker threads of concurrent.futures and cause hangs.
    with patch.object(_mod, 'get_proxy_for_scraping', return_value=proxy_return), \
         patch('concurrent.futures.ThreadPoolExecutor', _SyncExecutor), \
         patch('builtins.print'):
        scraper.scrape()

    return _db, _logger, _sources


# ═════════════════════════════════════════════════════════════════════════════
# __init__
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesScraperInit(unittest.TestCase):

    def _scraper(self):
        return SourcesScraper([1], 'srv', 'db', 'log', 'src', 'Germany')

    def test_get_sources_stored(self):
        self.assertEqual(self._scraper().get_sources, [1])

    def test_job_server_stored(self):
        self.assertEqual(self._scraper().job_server, 'srv')

    def test_db_stored(self):
        self.assertEqual(self._scraper().db, 'db')

    def test_logger_stored(self):
        self.assertEqual(self._scraper().logger, 'log')

    def test_sources_stored(self):
        self.assertEqual(self._scraper().sources, 'src')

    def test_country_stored(self):
        self.assertEqual(self._scraper().country, 'Germany')


# ═════════════════════════════════════════════════════════════════════════════
# scrape() — skip when already in progress
# ═════════════════════════════════════════════════════════════════════════════

class TestScrapeSkip(unittest.TestCase):

    def setUp(self):
        self.db, _, self.sources = _run(check_progress=True)

    def test_no_thread_spawned_when_skipped(self):
        self.sources.save_code.assert_not_called()

    def test_no_update_source_when_skipped(self):
        self.db.update_source.assert_not_called()

    def test_check_progress_called_with_url_and_result_id(self):
        self.db.check_progress.assert_called_once_with(_URL, 1)


# ═════════════════════════════════════════════════════════════════════════════
# scrape() — duplicate source
# ═════════════════════════════════════════════════════════════════════════════

class TestScrapeDuplicate(unittest.TestCase):

    def setUp(self):
        self.db, _, self.sources = _run(source_id_check=99)

    def test_update_result_source_called_for_duplicate(self):
        self.db.update_result_source.assert_called()

    def test_no_thread_for_duplicate(self):
        self.sources.save_code.assert_not_called()

    def test_update_result_source_uses_duplicate_id(self):
        args = self.db.update_result_source.call_args[0]
        self.assertIn(99, args)


# ═════════════════════════════════════════════════════════════════════════════
# scrape() — source_id is False (no result_source entry)
# ═════════════════════════════════════════════════════════════════════════════

class TestScrapeNoSourceId(unittest.TestCase):

    def setUp(self):
        self.db, _, self.sources = _run(
            source_id_by_result=False,
        )

    def test_no_save_code_called(self):
        self.sources.save_code.assert_not_called()

    def test_no_update_source_called(self):
        self.db.update_source.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# scrape() — no proxy available for foreign country
# ═════════════════════════════════════════════════════════════════════════════

class TestScrapeNoProxy(unittest.TestCase):

    def setUp(self):
        # country_proxy='US' != country='Germany', proxy=None → skip with progress=-1
        self.db, _, self.sources = _run(
            proxy_return=(None, 'no proxies'),
            country_proxy='US',
            country='Germany',
        )

    def test_no_thread_when_no_proxy(self):
        self.sources.save_code.assert_not_called()

    def test_update_source_called_with_minus_one(self):
        args = self.db.update_source.call_args[0]
        progress = args[2]
        self.assertEqual(progress, -1)

    def test_update_result_source_called_with_minus_one(self):
        args = self.db.update_result_source.call_args[0]
        progress = args[2]
        self.assertEqual(progress, -1)


# ═════════════════════════════════════════════════════════════════════════════
# scrape() — progress determination
# ═════════════════════════════════════════════════════════════════════════════

class TestScrapeProgress(unittest.TestCase):

    def _progress_from_update_source(self, db):
        return db.update_source.call_args[0][2]

    def test_progress_1_on_success(self):
        db, _, _ = _run()
        self.assertEqual(self._progress_from_update_source(db), 1)

    def test_progress_minus_one_on_bad_status(self):
        result = dict(_GOOD_RESULT, request={'content_type': 'html', 'status_code': 404})
        db, _, _ = _run(save_result=result)
        self.assertEqual(self._progress_from_update_source(db), -1)

    def test_progress_minus_one_on_error_content_type(self):
        result = dict(_GOOD_RESULT, request={'content_type': 'error', 'status_code': 200})
        db, _, _ = _run(save_result=result)
        self.assertEqual(self._progress_from_update_source(db), -1)

    def test_progress_minus_one_when_file_path_none(self):
        result = dict(_GOOD_RESULT, file_path=None)
        db, _, _ = _run(save_result=result)
        self.assertEqual(self._progress_from_update_source(db), -1)

    def test_progress_minus_one_on_timeout_in_error_codes(self):
        result = dict(_GOOD_RESULT, error_codes='Scraping timed out after 450s')
        db, _, _ = _run(save_result=result)
        self.assertEqual(self._progress_from_update_source(db), -1)

    def test_progress_minus_one_on_partial_content_in_error_codes(self):
        result = dict(_GOOD_RESULT, error_codes='Partial content saved')
        db, _, _ = _run(save_result=result)
        self.assertEqual(self._progress_from_update_source(db), -1)


# ═════════════════════════════════════════════════════════════════════════════
# scrape() — DB calls after successful scrape
# ═════════════════════════════════════════════════════════════════════════════

class TestScrapeDbCalls(unittest.TestCase):

    def setUp(self):
        self.db, _, _ = _run()

    def test_update_source_called(self):
        self.db.update_source.assert_called()

    def test_update_result_source_called(self):
        self.db.update_result_source.assert_called()

    def test_update_result_called(self):
        self.db.update_result.assert_called()

    def test_proxy_error_appended_to_error_code(self):
        result = dict(_GOOD_RESULT, error_codes='original error')
        db, _, _ = _run(save_result=result, proxy_return=(None, 'proxy failed'))
        error_code_arg = db.update_source.call_args[0][4]
        self.assertIn('proxy failed', error_code_arg)


if __name__ == '__main__':
    unittest.main()
