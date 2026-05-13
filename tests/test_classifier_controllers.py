"""
Unit tests for classifier_controller_start.py and classifier_controller_stop.py

classifier_controller_start  — ClassifierController.start()
    Spawns two threads: one for job_classifier.py, one for job_reset_classifier.py.

classifier_controller_stop   — ClassifierController.stop()
    Iterates psutil processes and kills those matching a hardcoded list; also kills
    browser processes once a classifier process was killed.  Sleeps 60 s, then calls
    db.reset(job_server).  Note: db and job_server are not method arguments — they
    are expected to exist as module-level globals (populated by __main__).
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ── Path setup ───────────────────────────────────────────────────────────────
_CLASSIFIER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'classifier',
)
sys.path.insert(0, _CLASSIFIER_DIR)

# classifier_controller_stop imports `from libs.lib_helper import Helper` and
# `from libs.lib_db import DB` as a package (libs is a sub-directory).
# Stub the whole package so the import succeeds without a real DB connection.
_libs_pkg = types.ModuleType('libs')
_libs_pkg.__path__ = [os.path.join(_CLASSIFIER_DIR, 'libs')]
sys.modules.setdefault('libs', _libs_pkg)

for _stub_name, _attr in [('libs.lib_helper', 'Helper'), ('libs.lib_db', 'DB')]:
    if _stub_name not in sys.modules:
        _m = types.ModuleType(_stub_name)
        setattr(_m, _attr, type(_attr, (), {}))
        sys.modules[_stub_name] = _m
        setattr(_libs_pkg, _stub_name.split('.')[-1], _m)

import classifier_controller_start as ccs_start
from classifier_controller_start import ClassifierController as StartController
from classifier_controller_stop  import ClassifierController as StopController


# ═════════════════════════════════════════════════════════════════════════════
# classifier_controller_start
# ═════════════════════════════════════════════════════════════════════════════

class TestClassifierControllerStart(unittest.TestCase):

    # ── Thread creation ───────────────────────────────────────────────────────

    @patch('classifier_controller_start.threading.Thread')
    def test_start_creates_exactly_two_threads(self, mock_thread):
        mock_thread.return_value = MagicMock()
        StartController().start('/some/dir')
        self.assertEqual(mock_thread.call_count, 2)

    @patch('classifier_controller_start.threading.Thread')
    def test_start_starts_both_threads(self, mock_thread):
        instance = MagicMock()
        mock_thread.return_value = instance
        StartController().start('/some/dir')
        self.assertEqual(instance.start.call_count, 2)

    @patch('classifier_controller_start.threading.Thread')
    def test_threads_created_with_callable_targets(self, mock_thread):
        mock_thread.return_value = MagicMock()
        StartController().start('/some/dir')
        for call_kwargs in mock_thread.call_args_list:
            target = call_kwargs[1].get('target') or call_kwargs[0][0]
            self.assertTrue(callable(target))

    # ── Command format ────────────────────────────────────────────────────────

    @patch('classifier_controller_start.os.system')
    @patch('classifier_controller_start.threading.Thread')
    def test_classifier_job_uses_correct_path(self, mock_thread, mock_system):
        workingdir = '/test/workingdir'
        captured = []

        def capture(target):
            captured.append(target)
            return MagicMock()

        mock_thread.side_effect = capture
        StartController().start(workingdir)

        for fn in captured:
            fn()

        commands = [c[0][0] for c in mock_system.call_args_list]
        self.assertTrue(any('job_classifier.py' in cmd for cmd in commands))

    @patch('classifier_controller_start.os.system')
    @patch('classifier_controller_start.threading.Thread')
    def test_reset_job_uses_correct_path(self, mock_thread, mock_system):
        workingdir = '/test/workingdir'
        captured = []

        def capture(target):
            captured.append(target)
            return MagicMock()

        mock_thread.side_effect = capture
        StartController().start(workingdir)

        for fn in captured:
            fn()

        commands = [c[0][0] for c in mock_system.call_args_list]
        self.assertTrue(any('job_reset_classifier.py' in cmd for cmd in commands))

    @patch('classifier_controller_start.os.system')
    @patch('classifier_controller_start.threading.Thread')
    def test_commands_contain_workingdir(self, mock_thread, mock_system):
        workingdir = '/my/custom/workingdir'
        captured = []

        def capture(target):
            captured.append(target)
            return MagicMock()

        mock_thread.side_effect = capture
        StartController().start(workingdir)

        for fn in captured:
            fn()

        commands = [c[0][0] for c in mock_system.call_args_list]
        for cmd in commands:
            self.assertIn(workingdir, cmd)

    @patch('classifier_controller_start.os.system')
    @patch('classifier_controller_start.threading.Thread')
    def test_commands_start_with_python(self, mock_thread, mock_system):
        captured = []

        def capture(target):
            captured.append(target)
            return MagicMock()

        mock_thread.side_effect = capture
        StartController().start('/dir')

        for fn in captured:
            fn()

        for c in mock_system.call_args_list:
            self.assertTrue(c[0][0].startswith('python '))

    @patch('classifier_controller_start.os.system')
    @patch('classifier_controller_start.threading.Thread')
    def test_two_distinct_commands_issued(self, mock_thread, mock_system):
        captured = []

        def capture(target):
            captured.append(target)
            return MagicMock()

        mock_thread.side_effect = capture
        StartController().start('/dir')

        for fn in captured:
            fn()

        commands = [c[0][0] for c in mock_system.call_args_list]
        self.assertEqual(len(set(commands)), 2, "Expected two distinct os.system calls")


# ═════════════════════════════════════════════════════════════════════════════
# classifier_controller_stop  —  helpers
# ═════════════════════════════════════════════════════════════════════════════

def _make_proc(name='python3', cmdline=None, raise_on_kill=False):
    """Build a fake psutil process object."""
    proc = MagicMock()
    proc.info = {'pid': 1234, 'name': name, 'cmdline': cmdline or []}
    if raise_on_kill:
        proc.kill.side_effect = Exception("process gone")
    return proc


def _run_stop(browser_list=None, procs=None, db=None, job_server='srv'):
    """
    Patches time.sleep and psutil.process_iter, then calls stop() with
    args = [browsers, db, job_server] as the production __main__ block does.
    Returns (db_mock, sleep_mock).
    """
    if db is None:
        db = MagicMock()

    with patch('classifier_controller_stop.time.sleep') as mock_sleep, \
         patch('classifier_controller_stop.psutil.process_iter', return_value=procs or []):
        StopController().stop([browser_list or [], db, job_server])
        return db, mock_sleep


# ═════════════════════════════════════════════════════════════════════════════
# classifier_controller_stop
# ═════════════════════════════════════════════════════════════════════════════

class TestClassifierControllerStop(unittest.TestCase):

    # ── Process killing ───────────────────────────────────────────────────────

    def test_kills_job_classifier_process(self):
        proc = _make_proc('python3', ['python3', 'job_classifier.py'])
        _run_stop(procs=[proc])
        proc.kill.assert_called_once()

    def test_kills_classifier_reset_process(self):
        proc = _make_proc('python3', ['python3', 'job_reset_classifier.py'])
        _run_stop(procs=[proc])
        proc.kill.assert_called_once()

    def test_kills_classifier_controller_start_process(self):
        proc = _make_proc('python3', ['python3', 'classifier_controller_start.py'])
        _run_stop(procs=[proc])
        proc.kill.assert_called_once()

    def test_does_not_kill_unrelated_python_process(self):
        proc = _make_proc('python3', ['python3', 'my_app.py'])
        _run_stop(procs=[proc])
        proc.kill.assert_not_called()

    def test_does_not_kill_non_python_process(self):
        proc = _make_proc('nginx', ['nginx', '-g', 'daemon off;'])
        _run_stop(procs=[proc])
        proc.kill.assert_not_called()

    def test_kills_browser_after_classifier_process_found(self):
        classifier_proc = _make_proc('python3', ['python3', 'job_classifier.py'])
        browser_proc    = _make_proc('chromium', ['chromium', '--no-sandbox'])
        _run_stop(browser_list=['chromium'], procs=[classifier_proc, browser_proc])
        classifier_proc.kill.assert_called()
        browser_proc.kill.assert_called()

    def test_does_not_kill_browser_if_no_classifier_process_found(self):
        browser_proc = _make_proc('chromium', ['chromium'])
        _run_stop(browser_list=['chromium'], procs=[browser_proc])
        browser_proc.kill.assert_not_called()

    def test_kills_multiple_matching_processes(self):
        proc1 = _make_proc('python3', ['python3', 'job_classifier.py'])
        proc2 = _make_proc('python3', ['python3', 'classifier_reset.py'])
        _run_stop(procs=[proc1, proc2])
        proc1.kill.assert_called()
        proc2.kill.assert_called()

    # ── Exception handling ────────────────────────────────────────────────────

    def test_exception_on_kill_does_not_crash(self):
        proc = _make_proc('python3', ['python3', 'job_classifier.py'], raise_on_kill=True)
        try:
            _run_stop(procs=[proc])
        except Exception:
            self.fail("stop() raised an exception despite the try/except guard")

    def test_none_cmdline_does_not_crash(self):
        proc = _make_proc('python3', cmdline=None)
        proc.info['cmdline'] = None
        try:
            _run_stop(procs=[proc])
        except Exception:
            self.fail("stop() raised when cmdline was None")

    def test_process_iter_exception_handled_gracefully(self):
        bad_proc = MagicMock()
        bad_proc.info = {'pid': 99, 'name': 'python3', 'cmdline': ['job_classifier.py']}
        bad_proc.kill.side_effect = Exception("access denied")
        try:
            _run_stop(procs=[bad_proc])
        except Exception:
            self.fail("stop() should swallow per-process exceptions")

    # ── sleep + db.reset ──────────────────────────────────────────────────────

    def test_sleep_called_before_db_reset(self):
        db_mock = MagicMock()
        call_order = []

        with patch('classifier_controller_stop.time.sleep',
                   side_effect=lambda _: call_order.append('sleep')), \
             patch('classifier_controller_stop.psutil.process_iter', return_value=[]):
            db_mock.reset.side_effect = lambda *a: call_order.append('reset')
            StopController().stop([[], db_mock, 'server1'])

        self.assertEqual(call_order, ['sleep', 'reset'])

    def test_sleep_duration_is_60_seconds(self):
        _, mock_sleep = _run_stop()
        mock_sleep.assert_called_once_with(60)

    def test_db_reset_called_with_job_server(self):
        db_mock = MagicMock()
        _run_stop(db=db_mock, job_server='my_server')
        db_mock.reset.assert_called_once_with('my_server')

    def test_db_reset_called_even_with_no_processes(self):
        db_mock, _ = _run_stop(procs=[])
        db_mock.reset.assert_called_once()

    # ── Empty / edge inputs ───────────────────────────────────────────────────

    def test_no_processes_does_not_crash(self):
        try:
            _run_stop(procs=[])
        except Exception:
            self.fail("stop() raised with an empty process list")

    def test_empty_browser_list_does_not_crash(self):
        proc = _make_proc('python3', ['python3', 'job_classifier.py'])
        try:
            _run_stop(browser_list=[], procs=[proc])
        except Exception:
            self.fail("stop() raised with an empty browser list")


if __name__ == '__main__':
    unittest.main()
