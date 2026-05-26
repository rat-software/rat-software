"""
Unit tests for rat-backend/query_sampler/query_sampler_reset.py

QSReset.reset()
    1. Calls reset_hanging_qs_jobs() to clear status-2 keywords.
    2. Calls get_keywords_bg() to check for remaining pending keywords.
    3. Prints an info message when pending keywords remain,
       or a clean-state message when there are none.
"""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Path / db stub ────────────────────────────────────────────────────────────
_QS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'query_sampler',
)
_RESET_PATH = os.path.join(_QS_DIR, 'query_sampler_reset.py')

_db_stub = types.ModuleType('db')
_db_stub.reset_hanging_qs_jobs = MagicMock()
_db_stub.get_keywords_bg       = MagicMock(return_value=[])
sys.modules['db'] = _db_stub

_spec = importlib.util.spec_from_file_location('query_sampler_reset', _RESET_PATH)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules['query_sampler_reset'] = _mod

from query_sampler_reset import QSReset


# ── Helper ────────────────────────────────────────────────────────────────────

def _run_reset(pending=None):
    """
    Call QSReset().reset() with mocked db functions.
    pending: list returned by get_keywords_bg (default empty).
    Returns (mock_reset_hanging, mock_get_bg, printed_output).
    """
    printed = []
    with patch('query_sampler_reset.reset_hanging_qs_jobs') as mock_reset, \
         patch('query_sampler_reset.get_keywords_bg',
               return_value=pending if pending is not None else []) as mock_bg, \
         patch('builtins.print', side_effect=lambda *a, **k: printed.append(' '.join(str(x) for x in a))):
        QSReset().reset()
    return mock_reset, mock_bg, printed


# ═════════════════════════════════════════════════════════════════════════════
# Initialisation
# ═════════════════════════════════════════════════════════════════════════════

class TestQSResetInit(unittest.TestCase):

    def test_instantiation_succeeds(self):
        qs = QSReset()
        self.assertIsInstance(qs, QSReset)

    def test_has_reset_method(self):
        self.assertTrue(callable(QSReset().reset))


# ═════════════════════════════════════════════════════════════════════════════
# reset() — DB calls
# ═════════════════════════════════════════════════════════════════════════════

class TestQSResetDbCalls(unittest.TestCase):

    def test_reset_hanging_qs_jobs_called(self):
        mock_reset, _, _ = _run_reset()
        mock_reset.assert_called_once()

    def test_get_keywords_bg_called(self):
        _, mock_bg, _ = _run_reset()
        mock_bg.assert_called_once()

    def test_reset_hanging_called_before_get_keywords_bg(self):
        call_order = []
        with patch('query_sampler_reset.reset_hanging_qs_jobs',
                   side_effect=lambda: call_order.append('reset')), \
             patch('query_sampler_reset.get_keywords_bg',
                   side_effect=lambda: call_order.append('get') or []), \
             patch('builtins.print'):
            QSReset().reset()
        self.assertEqual(call_order, ['reset', 'get'])


# ═════════════════════════════════════════════════════════════════════════════
# reset() — output when pending keywords exist
# ═════════════════════════════════════════════════════════════════════════════

class TestQSResetWithPendingKeywords(unittest.TestCase):

    def setUp(self):
        self.pending = [{'keyword_id': 1}, {'keyword_id': 2}, {'keyword_id': 3}]
        _, _, self.printed = _run_reset(pending=self.pending)

    def test_prints_pending_count(self):
        output = ' '.join(self.printed)
        self.assertIn('3', output)

    def test_prints_info_about_pending_keywords(self):
        output = ' '.join(self.printed)
        self.assertIn('pending', output.lower())

    def test_mentions_google_ads_yaml_when_pending(self):
        output = ' '.join(self.printed)
        self.assertIn('google-ads.yaml', output)

    def test_does_not_print_clean_state_message(self):
        output = ' '.join(self.printed)
        self.assertNotIn('up to date', output)


# ═════════════════════════════════════════════════════════════════════════════
# reset() — output when no pending keywords
# ═════════════════════════════════════════════════════════════════════════════

class TestQSResetNoPendingKeywords(unittest.TestCase):

    def setUp(self):
        _, _, self.printed = _run_reset(pending=[])

    def test_prints_clean_state_message(self):
        output = ' '.join(self.printed)
        self.assertIn('up to date', output)

    def test_does_not_print_pending_count(self):
        output = ' '.join(self.printed)
        self.assertNotIn('google-ads.yaml', output)

    def test_does_not_print_keyword_count(self):
        # The pending-count message ("There are currently N QS keywords pending")
        # must not appear when there are no pending keywords.
        output = ' '.join(self.printed)
        self.assertNotIn('There are currently', output)


if __name__ == '__main__':
    unittest.main()
