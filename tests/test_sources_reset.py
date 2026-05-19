"""
Unit tests for rat-backend/sources/sources_reset.py

SourcesReset.reset(db, job_server)
    Iterates pending sources from db.get_sources_pending(job_server).
    For each entry (result_source_id, source_id, result_id, ...):
      - If source_id is truthy:
          writes to logger, increments counter, calls reset_result_source,
          calls delete_source_pending.
      - If source_id is falsy:
          writes to logger, calls delete_result_source_pending.
    Always calls db.update_sources_failed(job_server) at the end.
"""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, call, patch

# ── Stub libs (imported at module level via from libs.X import *) ─────────────
_SOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'sources',
)

_libs_pkg = types.ModuleType('libs')
_libs_pkg.__path__ = [os.path.join(_SOURCES_DIR, 'libs')]
sys.modules.setdefault('libs', _libs_pkg)

for _stub_name, _attr in [
    ('libs.lib_logger', 'Logger'),
    ('libs.lib_helper', 'Helper'),
    ('libs.lib_db',     'DB'),
]:
    if _stub_name not in sys.modules:
        _m = types.ModuleType(_stub_name)
        setattr(_m, _attr, type(_attr, (), {}))
        sys.modules[_stub_name] = _m
        setattr(_libs_pkg, _stub_name.split('.')[-1], _m)

# ── Load module ───────────────────────────────────────────────────────────────
_spec = importlib.util.spec_from_file_location(
    'sources_reset', os.path.join(_SOURCES_DIR, 'sources_reset.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules['sources_reset'] = _mod

from sources_reset import SourcesReset

_JOB_SERVER = 'worker-1'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_db(pending=None, counter=3):
    db = MagicMock()
    db.get_sources_pending.return_value       = pending or []
    db.get_source_counter_result.return_value = counter
    return db


def _make_logger():
    return MagicMock()


def _pending_row(result_source_id=10, source_id=99, result_id=5):
    """Build a fake pending-source tuple (result_source_id, source_id, result_id)."""
    return (result_source_id, source_id, result_id)


def _run(pending=None, counter=3):
    db     = _make_db(pending=pending, counter=counter)
    logger = _make_logger()
    with patch('builtins.print'):
        SourcesReset(db, logger).reset(db, _JOB_SERVER)
    return db, logger


# ═════════════════════════════════════════════════════════════════════════════
# Initialisation
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesResetInit(unittest.TestCase):

    def test_instantiation_succeeds(self):
        sr = SourcesReset(_make_db(), _make_logger())
        self.assertIsInstance(sr, SourcesReset)

    def test_db_stored_as_attribute(self):
        db = _make_db()
        sr = SourcesReset(db, _make_logger())
        self.assertIs(sr.db, db)

    def test_logger_stored_as_attribute(self):
        logger = _make_logger()
        sr = SourcesReset(_make_db(), logger)
        self.assertIs(sr.logger, logger)


# ═════════════════════════════════════════════════════════════════════════════
# reset() — DB entry point
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesResetDbCalls(unittest.TestCase):

    def test_get_sources_pending_called_with_job_server(self):
        db, _ = _run()
        db.get_sources_pending.assert_called_once_with(_JOB_SERVER)

    def test_update_sources_failed_always_called(self):
        db, _ = _run()
        db.update_sources_failed.assert_called_once_with(_JOB_SERVER)

    def test_update_sources_failed_called_when_no_pending(self):
        db, _ = _run(pending=[])
        db.update_sources_failed.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# reset() — source_id is truthy
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesResetWithSourceId(unittest.TestCase):

    def setUp(self):
        row          = _pending_row(result_source_id=10, source_id=99, result_id=5)
        self.db, self.logger = _run(pending=[row], counter=3)

    def test_logger_write_to_log_called(self):
        self.logger.write_to_log.assert_called()

    def test_log_contains_source_id(self):
        log_arg = self.logger.write_to_log.call_args[0][0]
        self.assertIn('99', log_arg)

    def test_get_source_counter_result_called_with_result_id(self):
        self.db.get_source_counter_result.assert_called_once_with(5)

    def test_counter_incremented_by_one(self):
        args = self.db.reset_result_source.call_args[0]
        # counter is the second positional arg
        self.assertEqual(args[1], 4)   # counter=3 + 1

    def test_reset_result_source_called_with_source_id(self):
        args = self.db.reset_result_source.call_args[0]
        self.assertIn(99, args)

    def test_reset_result_source_progress_is_zero(self):
        args = self.db.reset_result_source.call_args[0]
        self.assertEqual(args[0], 0)

    def test_delete_source_pending_called_with_source_id(self):
        args = self.db.delete_source_pending.call_args[0]
        self.assertIn(99, args)

    def test_delete_source_pending_progress_is_zero(self):
        args = self.db.delete_source_pending.call_args[0]
        self.assertEqual(args[1], 0)

    def test_delete_result_source_pending_not_called(self):
        self.db.delete_result_source_pending.assert_not_called()

    def test_processes_multiple_rows(self):
        rows = [
            _pending_row(result_source_id=1, source_id=10, result_id=1),
            _pending_row(result_source_id=2, source_id=20, result_id=2),
        ]
        db, _ = _run(pending=rows)
        self.assertEqual(db.reset_result_source.call_count, 2)
        self.assertEqual(db.delete_source_pending.call_count, 2)


# ═════════════════════════════════════════════════════════════════════════════
# reset() — source_id is falsy (None / 0)
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesResetWithoutSourceId(unittest.TestCase):

    def setUp(self):
        row = _pending_row(result_source_id=77, source_id=None, result_id=5)
        self.db, self.logger = _run(pending=[row])

    def test_logger_write_to_log_called(self):
        self.logger.write_to_log.assert_called()

    def test_delete_result_source_pending_called_with_result_source_id(self):
        self.db.delete_result_source_pending.assert_called_once_with(77)

    def test_reset_result_source_not_called(self):
        self.db.reset_result_source.assert_not_called()

    def test_delete_source_pending_not_called(self):
        self.db.delete_source_pending.assert_not_called()

    def test_get_source_counter_result_not_called(self):
        self.db.get_source_counter_result.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# reset() — call ordering
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesResetCallOrder(unittest.TestCase):

    def test_update_sources_failed_called_after_loop(self):
        call_order = []
        db     = MagicMock()
        logger = MagicMock()
        db.get_sources_pending.return_value       = [_pending_row(source_id=1, result_id=1)]
        db.get_source_counter_result.return_value = 0
        db.reset_result_source.side_effect        = lambda *a: call_order.append('reset')
        db.update_sources_failed.side_effect      = lambda *a: call_order.append('update_failed')

        with patch('builtins.print'):
            SourcesReset(db, logger).reset(db, _JOB_SERVER)

        self.assertEqual(call_order, ['reset', 'update_failed'])


if __name__ == '__main__':
    unittest.main()
