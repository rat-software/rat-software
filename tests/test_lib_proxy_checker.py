"""
Unit tests for rat-backend/sources/libs/lib_proxy_checker.py

Covers:
  - check_proxy:        success (200), non-200, timeout, connection error,
                        generic exception, proxy format, custom timeout
  - get_working_proxy:  missing CSV, unreadable CSV, empty CSV, valid CSV
                        parsing (empty rows, multi-column), all proxies fail,
                        max_attempts respected, first working proxy returned
  - get_proxy_for_scraping: proxy needed, not needed, None country_proxy
"""
import importlib.util
import io
import os
import sys
import unittest
from unittest.mock import MagicMock, call, patch

import requests

# ── Load module and register it so patch() strings resolve correctly ──────────
_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'sources', 'libs', 'lib_proxy_checker.py',
)
_spec = importlib.util.spec_from_file_location('lib_proxy_checker', _LIB_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules['lib_proxy_checker'] = _mod
_spec.loader.exec_module(_mod)

check_proxy        = _mod.check_proxy
get_working_proxy  = _mod.get_working_proxy
get_proxy_for_scraping = _mod.get_proxy_for_scraping


def _csv_open_mock(content: str):
    """Context-manager mock wrapping a StringIO — compatible with csv.reader."""
    m = MagicMock()
    m.__enter__ = MagicMock(return_value=io.StringIO(content))
    m.__exit__ = MagicMock(return_value=False)
    return m


# ─────────────────────────────────────────────────────────────────────────────
# check_proxy
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckProxySuccess(unittest.TestCase):

    @patch('lib_proxy_checker.requests.get')
    def test_200_returns_true(self, mock_get):
        mock_get.return_value.status_code = 200
        self.assertTrue(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get')
    def test_non_200_returns_false(self, mock_get):
        mock_get.return_value.status_code = 403
        self.assertFalse(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get')
    def test_404_returns_false(self, mock_get):
        mock_get.return_value.status_code = 404
        self.assertFalse(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get')
    def test_proxy_formatted_correctly(self, mock_get):
        mock_get.return_value.status_code = 200
        check_proxy('1.2.3.4:8080')
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs['proxies']['http'],  'http://1.2.3.4:8080')
        self.assertEqual(kwargs['proxies']['https'], 'http://1.2.3.4:8080')

    @patch('lib_proxy_checker.requests.get')
    def test_default_timeout_is_10(self, mock_get):
        mock_get.return_value.status_code = 200
        check_proxy('1.2.3.4:8080')
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs['timeout'], 10)

    @patch('lib_proxy_checker.requests.get')
    def test_custom_timeout_is_passed(self, mock_get):
        mock_get.return_value.status_code = 200
        check_proxy('1.2.3.4:8080', timeout=3)
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs['timeout'], 3)


class TestCheckProxyErrors(unittest.TestCase):

    @patch('lib_proxy_checker.requests.get',
           side_effect=requests.exceptions.Timeout)
    def test_timeout_returns_false(self, _):
        self.assertFalse(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get',
           side_effect=requests.exceptions.ConnectionError)
    def test_connection_error_returns_false(self, _):
        self.assertFalse(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get',
           side_effect=requests.exceptions.ProxyError)
    def test_proxy_error_returns_false(self, _):
        self.assertFalse(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get',
           side_effect=Exception('unexpected'))
    def test_generic_exception_returns_false(self, _):
        self.assertFalse(check_proxy('1.2.3.4:8080'))

    @patch('lib_proxy_checker.requests.get',
           side_effect=requests.exceptions.SSLError)
    def test_ssl_error_returns_false(self, _):
        self.assertFalse(check_proxy('1.2.3.4:8080'))


# ─────────────────────────────────────────────────────────────────────────────
# get_working_proxy — CSV parsing
# ─────────────────────────────────────────────────────────────────────────────

class TestGetWorkingProxyCSVParsing(unittest.TestCase):

    @patch('lib_proxy_checker.os.path.exists', return_value=False)
    def test_missing_csv_returns_none_and_error(self, _):
        proxy, err = get_working_proxy('DE')
        self.assertIsNone(proxy)
        self.assertIn('DE.csv', err)

    @patch('lib_proxy_checker.os.path.exists', return_value=True)
    @patch('builtins.open', side_effect=IOError('permission denied'))
    def test_unreadable_csv_returns_none_and_error(self, *_):
        proxy, err = get_working_proxy('DE')
        self.assertIsNone(proxy)
        self.assertIn('DE.csv', err)

    @patch('lib_proxy_checker.os.path.exists', return_value=True)
    @patch('builtins.open')
    def test_empty_csv_returns_none_and_error(self, mock_open, _):
        mock_open.return_value = _csv_open_mock('')
        proxy, err = get_working_proxy('DE')
        self.assertIsNone(proxy)
        self.assertIn('No proxies', err)

    @patch('lib_proxy_checker.os.path.exists', return_value=True)
    @patch('builtins.open')
    @patch('lib_proxy_checker.check_proxy', return_value=True)
    @patch('lib_proxy_checker.time.sleep')
    def test_reads_first_column_only(self, _sleep, mock_cp, mock_open, _exists):
        mock_open.return_value = _csv_open_mock('1.1.1.1:80,extra,data\n')
        proxy, err = get_working_proxy('DE', max_attempts=1)
        self.assertEqual(proxy, '1.1.1.1:80')

    @patch('lib_proxy_checker.os.path.exists', return_value=True)
    @patch('builtins.open')
    @patch('lib_proxy_checker.check_proxy', return_value=True)
    @patch('lib_proxy_checker.time.sleep')
    def test_skips_empty_rows(self, _sleep, mock_cp, mock_open, _exists):
        mock_open.return_value = _csv_open_mock('\n\n2.2.2.2:80\n\n')
        proxy, _ = get_working_proxy('DE', max_attempts=1)
        self.assertEqual(proxy, '2.2.2.2:80')


# ─────────────────────────────────────────────────────────────────────────────
# get_working_proxy — proxy validation logic
# ─────────────────────────────────────────────────────────────────────────────

class TestGetWorkingProxyValidation(unittest.TestCase):

    def _run(self, csv_content, check_results, max_attempts=3):
        with patch('lib_proxy_checker.os.path.exists', return_value=True), \
             patch('builtins.open', return_value=_csv_open_mock(csv_content)), \
             patch('lib_proxy_checker.check_proxy', side_effect=check_results), \
             patch('lib_proxy_checker.time.sleep'), \
             patch('lib_proxy_checker.random.shuffle'):   # keep order deterministic
            return get_working_proxy('DE', max_attempts=max_attempts)

    def test_first_working_proxy_returned(self):
        proxy, err = self._run('p1:80\np2:80\np3:80\n', [True, True, True])
        self.assertEqual(proxy, 'p1:80')
        self.assertEqual(err, '')

    def test_second_proxy_used_when_first_fails(self):
        proxy, err = self._run('p1:80\np2:80\n', [False, True])
        self.assertEqual(proxy, 'p2:80')

    def test_all_proxies_fail_returns_none(self):
        proxy, err = self._run('p1:80\np2:80\np3:80\n', [False, False, False])
        self.assertIsNone(proxy)
        self.assertIn('failed', err)

    def test_max_attempts_limits_checks(self):
        check_mock = MagicMock(return_value=False)
        with patch('lib_proxy_checker.os.path.exists', return_value=True), \
             patch('builtins.open',
                   return_value=_csv_open_mock('p1:80\np2:80\np3:80\np4:80\n')), \
             patch('lib_proxy_checker.check_proxy', check_mock), \
             patch('lib_proxy_checker.time.sleep'), \
             patch('lib_proxy_checker.random.shuffle'):
            get_working_proxy('DE', max_attempts=2)
        self.assertEqual(check_mock.call_count, 2)

    def test_error_message_includes_attempt_count(self):
        _, err = self._run('p1:80\np2:80\n', [False, False])
        self.assertIn('2', err)

    def test_single_working_proxy_in_file(self):
        proxy, err = self._run('only:80\n', [True])
        self.assertEqual(proxy, 'only:80')
        self.assertEqual(err, '')


# ─────────────────────────────────────────────────────────────────────────────
# get_proxy_for_scraping
# ─────────────────────────────────────────────────────────────────────────────

class TestGetProxyForScraping(unittest.TestCase):

    @patch('lib_proxy_checker.get_working_proxy', return_value=('1.1.1.1:80', ''))
    def test_different_country_triggers_proxy_lookup(self, mock_gwp):
        proxy, err = get_proxy_for_scraping('US', 'DE')
        mock_gwp.assert_called_once_with('US')
        self.assertEqual(proxy, '1.1.1.1:80')

    def test_same_country_returns_no_proxy(self):
        proxy, err = get_proxy_for_scraping('DE', 'DE')
        self.assertIsNone(proxy)
        self.assertEqual(err, '')

    def test_none_country_proxy_returns_no_proxy(self):
        proxy, err = get_proxy_for_scraping(None, 'DE')
        self.assertIsNone(proxy)
        self.assertEqual(err, '')

    @patch('lib_proxy_checker.get_working_proxy', return_value=(None, 'all failed'))
    def test_failed_proxy_lookup_propagates_error(self, _):
        proxy, err = get_proxy_for_scraping('US', 'DE')
        self.assertIsNone(proxy)
        self.assertEqual(err, 'all failed')


if __name__ == '__main__':
    unittest.main()
