"""
Unit tests for rat-backend/backend_controller_start.py
                and rat-backend/backend_controller_stop.py

backend_controller_start.py
    Module-level: computes absolute paths to three controller scripts.
    source() / classifier() / query_sampler(): each calls os.system("python <path>").

backend_controller_stop.py
    load_db_config(path)           — reads JSON from file
    terminate_processes(args)      — kills psutil procs whose cmdline matches
                                     'sources'/'classifier'/'scraper' + '.py';
                                     also kills browser procs (kill_browser always True)
    reset_classifiers(...)         — 3 DELETE statements via psycopg2
    update_pending_jobs(...)       — fetches orphaned classifier rows, resets each
    get_sources_pending(...)       — SELECT sources with progress=2
    delete_source_pending(...)     — DELETE from source
    reset_result_source(...)       — DELETE from result_source
"""

import importlib.util
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call, mock_open

# ── Paths ──────────────────────────────────────────────────────────────────────
_BACKEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend',
)

# ── psutil / psycopg2 stubs (needed before loading stop module) ────────────────
for _sname in ('psutil', 'psycopg2', 'psycopg2.extras'):
    if _sname not in sys.modules:
        _m = types.ModuleType(_sname)
        _m.__path__ = []
        sys.modules[_sname] = _m

# psutil — full stub so later test files can patch process_iter and raise
# exception instances with keyword arguments (pid=..., name=..., etc.)
def _psutil_exc(name):
    return type(name, (Exception,), {'__init__': lambda self, *a, **kw: Exception.__init__(self, *a)})

_psutil = sys.modules['psutil']
_psutil.process_iter  = MagicMock(return_value=[])
_psutil.NoSuchProcess = _psutil_exc('NoSuchProcess')
_psutil.AccessDenied  = _psutil_exc('AccessDenied')
_psutil.ZombieProcess = _psutil_exc('ZombieProcess')

# psycopg2 — add all symbols other test files need
_psycopg2 = sys.modules['psycopg2']
_psycopg2.OperationalError = type('OperationalError', (Exception,), {})
_psycopg2_extras = sys.modules['psycopg2.extras']
_psycopg2_extras.DictCursor     = type('DictCursor',     (), {})
_psycopg2_extras.RealDictCursor = type('RealDictCursor', (), {})
_psycopg2_extras.execute_values = MagicMock()
setattr(_psycopg2, 'extras', _psycopg2_extras)
setattr(_psycopg2, 'connect', MagicMock())

# ── Load modules ───────────────────────────────────────────────────────────────

def _load(filename, modname):
    spec = importlib.util.spec_from_file_location(
        modname, os.path.join(_BACKEND_DIR, filename)
    )
    mod = importlib.util.module_from_spec(spec)
    with patch('builtins.print'):
        spec.loader.exec_module(mod)
    sys.modules[modname] = mod
    return mod

bc_start = _load('backend_controller_start.py', 'backend_controller_start')
bc_stop  = _load('backend_controller_stop.py',  'backend_controller_stop')


# ── psycopg2 connection helper ─────────────────────────────────────────────────

def _make_pg(rows=None):
    """Return (conn_mock, cursor_mock) — conn usable as context manager."""
    cur = MagicMock()
    cur.fetchall.return_value = rows or []

    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__  = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__  = MagicMock(return_value=False)
    return conn, cur


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_start — module-level paths
# ═════════════════════════════════════════════════════════════════════════════

class TestBackendControllerStartPaths(unittest.TestCase):

    def test_sources_controller_path_ends_with_correct_file(self):
        self.assertTrue(bc_start.sources_controller.endswith('sources_controller_start.py'))

    def test_classifier_controller_path_ends_with_correct_file(self):
        self.assertTrue(bc_start.classifier_controller.endswith('classifier_controller_start.py'))

    def test_query_sampler_controller_path_ends_with_correct_file(self):
        self.assertTrue(bc_start.query_sampler_controller.endswith('query_sampler_controller_start.py'))

    def test_paths_are_absolute(self):
        for p in [bc_start.sources_controller,
                  bc_start.classifier_controller,
                  bc_start.query_sampler_controller]:
            self.assertTrue(os.path.isabs(p))


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_start — source / classifier / query_sampler functions
# ═════════════════════════════════════════════════════════════════════════════

class TestBackendControllerStartFunctions(unittest.TestCase):

    def _run(self, fn):
        with patch.object(bc_start.os, 'system') as mock_sys, \
             patch('builtins.print'):
            fn()
        return mock_sys

    def test_source_calls_os_system_once(self):
        self._run(bc_start.source).assert_called_once()

    def test_source_command_starts_with_python(self):
        m = self._run(bc_start.source)
        self.assertTrue(m.call_args[0][0].startswith('python '))

    def test_source_command_targets_sources_controller(self):
        m = self._run(bc_start.source)
        self.assertIn('sources_controller_start.py', m.call_args[0][0])

    def test_classifier_calls_os_system_once(self):
        self._run(bc_start.classifier).assert_called_once()

    def test_classifier_command_targets_classifier_controller(self):
        m = self._run(bc_start.classifier)
        self.assertIn('classifier_controller_start.py', m.call_args[0][0])

    def test_query_sampler_calls_os_system_once(self):
        self._run(bc_start.query_sampler).assert_called_once()

    def test_query_sampler_command_targets_qs_controller(self):
        m = self._run(bc_start.query_sampler)
        self.assertIn('query_sampler_controller_start.py', m.call_args[0][0])

    def test_three_functions_target_distinct_scripts(self):
        cmds = set()
        for fn in [bc_start.source, bc_start.classifier, bc_start.query_sampler]:
            with patch.object(bc_start.os, 'system') as m:
                fn()
            cmds.add(m.call_args[0][0])
        self.assertEqual(len(cmds), 3)


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_stop — load_db_config
# ═════════════════════════════════════════════════════════════════════════════

class TestLoadDbConfig(unittest.TestCase):

    def test_returns_parsed_json(self):
        data = {'host': 'localhost', 'port': 5432}
        m = mock_open(read_data=json.dumps(data))
        with patch('builtins.open', m), \
             patch('backend_controller_stop.json.load', return_value=data):
            result = bc_stop.load_db_config('/fake/path.json')
        self.assertEqual(result, data)

    def test_opens_correct_path(self):
        m = mock_open(read_data='{}')
        with patch('builtins.open', m), \
             patch('backend_controller_stop.json.load', return_value={}):
            bc_stop.load_db_config('/some/config.json')
        m.assert_called_once_with('/some/config.json', encoding='utf-8')


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_stop — terminate_processes
# ═════════════════════════════════════════════════════════════════════════════

def _make_proc(name='python3', cmdline=None):
    proc = MagicMock()
    proc.info = {
        'pid':     999,
        'name':    name,
        'cmdline': cmdline if cmdline is not None else [],
    }
    return proc


def _run_terminate(procs=None, args=None):
    with patch('backend_controller_stop.psutil.process_iter',
               return_value=procs or [], create=True), \
         patch('builtins.print'):
        bc_stop.terminate_processes(args or [])


class TestTerminateProcesses(unittest.TestCase):

    # ── keyword matching ──────────────────────────────────────────────────────

    def test_kills_proc_with_sources_in_cmdline(self):
        proc = _make_proc('python3', ['python3', 'sources_controller_start.py'])
        _run_terminate([proc])
        proc.kill.assert_called()

    def test_kills_proc_with_classifier_in_cmdline(self):
        proc = _make_proc('python3', ['python3', 'classifier_controller_start.py'])
        _run_terminate([proc])
        proc.kill.assert_called()

    def test_kills_proc_with_scraper_in_cmdline(self):
        proc = _make_proc('python3', ['python3', 'sources_scraper.py'])
        _run_terminate([proc])
        proc.kill.assert_called()

    def test_does_not_kill_proc_without_matching_keyword(self):
        proc = _make_proc('python3', ['python3', 'my_other_app.py'])
        _run_terminate([proc])
        proc.kill.assert_not_called()

    def test_does_not_kill_proc_without_py_extension(self):
        # keyword present but no '.py' suffix
        proc = _make_proc('python3', ['python3', 'sources_binary'])
        _run_terminate([proc])
        proc.kill.assert_not_called()

    # ── browser killing (kill_browser starts True) ────────────────────────────

    def test_kills_browser_by_name_match(self):
        browser = _make_proc('chromium', ['chromium'])
        _run_terminate([browser], args=['chromium'])
        browser.kill.assert_called()

    def test_does_not_kill_browser_not_in_args(self):
        browser = _make_proc('firefox', ['firefox'])
        _run_terminate([browser], args=['chromium'])
        browser.kill.assert_not_called()

    # ── exception handling ────────────────────────────────────────────────────

    def test_kill_exception_does_not_crash(self):
        proc = _make_proc('python3', ['python3', 'sources_scraper.py'])
        proc.kill.side_effect = Exception('access denied')
        try:
            _run_terminate([proc])
        except Exception:
            self.fail('terminate_processes should swallow kill exceptions')

    def test_none_cmdline_does_not_crash(self):
        proc = _make_proc('python3')
        proc.info['cmdline'] = None
        try:
            _run_terminate([proc])
        except Exception:
            self.fail('terminate_processes should handle None cmdline')


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_stop — reset_classifiers
# ═════════════════════════════════════════════════════════════════════════════

class TestResetClassifiers(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _make_pg()
        with patch('backend_controller_stop.psycopg2.connect', return_value=self.conn):
            bc_stop.reset_classifiers('result-1', {'host': 'localhost'}, 'srv')

    def test_three_statements_executed(self):
        self.assertEqual(self.cur.execute.call_count, 3)

    def test_deletes_classifier_indicator(self):
        calls = [c[0][0] for c in self.cur.execute.call_args_list]
        self.assertTrue(any('classifier_indicator' in s for s in calls))

    def test_deletes_classifier_result(self):
        calls = [c[0][0] for c in self.cur.execute.call_args_list]
        self.assertTrue(any('classifier_result' in s for s in calls))

    def test_commit_called(self):
        self.conn.commit.assert_called()

    def test_result_id_passed_to_query(self):
        all_args = [c[0][1] for c in self.cur.execute.call_args_list]
        self.assertTrue(any('result-1' in str(a) for a in all_args))


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_stop — update_pending_jobs
# ═════════════════════════════════════════════════════════════════════════════

class TestUpdatePendingJobs(unittest.TestCase):

    def test_calls_reset_classifiers_for_each_orphaned_result(self):
        rows = [{'result': 'r1'}, {'result': 'r2'}]
        conn, _ = _make_pg(rows=rows)
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn), \
             patch.object(bc_stop, 'reset_classifiers') as mock_reset:
            bc_stop.update_pending_jobs({'host': 'localhost'}, 'srv')
        self.assertEqual(mock_reset.call_count, 2)

    def test_no_reset_when_no_orphaned_results(self):
        conn, _ = _make_pg(rows=[])
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn), \
             patch.object(bc_stop, 'reset_classifiers') as mock_reset:
            bc_stop.update_pending_jobs({'host': 'localhost'}, 'srv')
        mock_reset.assert_not_called()

    def test_passes_result_id_to_reset_classifiers(self):
        rows = [{'result': 'abc'}]
        conn, _ = _make_pg(rows=rows)
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn), \
             patch.object(bc_stop, 'reset_classifiers') as mock_reset:
            bc_stop.update_pending_jobs({'host': 'db'}, 'srv')
        mock_reset.assert_called_once_with('abc', {'host': 'db'}, 'srv')


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_stop — get_sources_pending
# ═════════════════════════════════════════════════════════════════════════════

class TestGetSourcesPending(unittest.TestCase):

    def test_returns_rows_from_db(self):
        rows = [{'id': 1, 'created_at': 'now'}, {'id': 2, 'created_at': 'then'}]
        conn, _ = _make_pg(rows=rows)
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn):
            result = bc_stop.get_sources_pending({'host': 'db'}, 'srv')
        self.assertEqual(result, rows)

    def test_returns_empty_list_when_no_pending(self):
        conn, _ = _make_pg(rows=[])
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn):
            result = bc_stop.get_sources_pending({'host': 'db'}, 'srv')
        self.assertEqual(result, [])

    def test_query_filters_by_progress_2(self):
        conn, cur = _make_pg()
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn):
            bc_stop.get_sources_pending({'host': 'db'}, 'srv')
        sql = cur.execute.call_args[0][0]
        self.assertIn('progress = 2', sql)


# ═════════════════════════════════════════════════════════════════════════════
# backend_controller_stop — delete_source_pending / reset_result_source
# ═════════════════════════════════════════════════════════════════════════════

class TestDeleteAndReset(unittest.TestCase):

    def _run_with_cur(self, fn, *args):
        conn, cur = _make_pg()
        with patch('backend_controller_stop.psycopg2.connect', return_value=conn):
            fn(*args)
        return conn, cur

    def test_delete_source_pending_executes_delete(self):
        _, cur = self._run_with_cur(bc_stop.delete_source_pending, 7, {'host': 'db'}, 'srv')
        sql = cur.execute.call_args[0][0]
        self.assertIn('DELETE', sql.upper())
        self.assertIn('source', sql)

    def test_delete_source_pending_passes_source_id(self):
        _, cur = self._run_with_cur(bc_stop.delete_source_pending, 42, {'host': 'db'}, 'srv')
        params = cur.execute.call_args[0][1]
        self.assertIn(42, params)

    def test_delete_source_pending_commits(self):
        conn, _ = self._run_with_cur(bc_stop.delete_source_pending, 7, {'host': 'db'}, 'srv')
        conn.commit.assert_called()

    def test_reset_result_source_executes_delete(self):
        _, cur = self._run_with_cur(bc_stop.reset_result_source, 5, {'host': 'db'}, 'srv')
        sql = cur.execute.call_args[0][0]
        self.assertIn('DELETE', sql.upper())
        self.assertIn('result_source', sql)

    def test_reset_result_source_passes_source_id(self):
        _, cur = self._run_with_cur(bc_stop.reset_result_source, 99, {'host': 'db'}, 'srv')
        params = cur.execute.call_args[0][1]
        self.assertIn(99, params)

    def test_reset_result_source_commits(self):
        conn, _ = self._run_with_cur(bc_stop.reset_result_source, 5, {'host': 'db'}, 'srv')
        conn.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
