"""
Unit tests for rat-backend/sources/libs/lib_logger.py

Logger.write_to_log(log)
    Opens 'sources_scraper.log' in append mode and writes
    "{DD-MM-YYYY, HH:MM:SS}: {log}\n".
"""

import importlib.util
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch, mock_open, call

# ── Load module ───────────────────────────────────────────────────────────────
_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'rat-backend', 'sources', 'libs', 'lib_logger.py',
)
_spec = importlib.util.spec_from_file_location('lib_logger', _LIB_PATH)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules['lib_logger'] = _mod

from lib_logger import Logger

_FIXED_DT  = datetime(2024, 6, 15, 9, 5, 3)
_FIXED_STR = '15-06-2024, 09:05:03'


def _write(msg='hello', fixed_dt=_FIXED_DT):
    """Call write_to_log with a mocked datetime and mocked open; return written string."""
    m = mock_open()
    with patch('builtins.open', m), \
         patch('lib_logger.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_dt
        Logger().write_to_log(msg)
    return m().write.call_args[0][0]


# ═════════════════════════════════════════════════════════════════════════════
# Instantiation
# ═════════════════════════════════════════════════════════════════════════════

class TestLoggerInit(unittest.TestCase):

    def test_instantiation_succeeds(self):
        self.assertIsInstance(Logger(), Logger)

    def test_has_write_to_log_method(self):
        self.assertTrue(callable(Logger().write_to_log))


# ═════════════════════════════════════════════════════════════════════════════
# File handling
# ═════════════════════════════════════════════════════════════════════════════

class TestLoggerFileHandling(unittest.TestCase):

    def test_opens_correct_filename(self):
        m = mock_open()
        with patch('builtins.open', m), patch('lib_logger.datetime'):
            Logger().write_to_log('x')
        self.assertEqual(m.call_args[0][0], 'sources_scraper.log')

    def test_opens_in_append_mode(self):
        m = mock_open()
        with patch('builtins.open', m), patch('lib_logger.datetime'):
            Logger().write_to_log('x')
        self.assertEqual(m.call_args[0][1], 'a')

    def test_write_called_once_per_log_call(self):
        m = mock_open()
        with patch('builtins.open', m), patch('lib_logger.datetime'):
            Logger().write_to_log('x')
        m().write.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# Written content
# ═════════════════════════════════════════════════════════════════════════════

class TestLoggerContent(unittest.TestCase):

    def test_log_message_in_output(self):
        written = _write('my log message')
        self.assertIn('my log message', written)

    def test_timestamp_format_dd_mm_yyyy(self):
        written = _write(fixed_dt=_FIXED_DT)
        self.assertIn(_FIXED_STR, written)

    def test_timestamp_precedes_message(self):
        written = _write('msg', fixed_dt=_FIXED_DT)
        ts_pos  = written.index(_FIXED_STR)
        msg_pos = written.index('msg')
        self.assertLess(ts_pos, msg_pos)

    def test_colon_separator_between_timestamp_and_message(self):
        written = _write('msg', fixed_dt=_FIXED_DT)
        self.assertIn(f'{_FIXED_STR}: msg', written)

    def test_output_ends_with_newline(self):
        written = _write('anything')
        self.assertTrue(written.endswith('\n'))

    def test_different_messages_written_correctly(self):
        written = _write('Reset \t source \t 42')
        self.assertIn('Reset \t source \t 42', written)

    def test_multiple_calls_each_write_to_file(self):
        m = mock_open()
        with patch('builtins.open', m), patch('lib_logger.datetime'):
            logger = Logger()
            logger.write_to_log('first')
            logger.write_to_log('second')
        self.assertEqual(m().write.call_count, 2)


if __name__ == '__main__':
    unittest.main()
