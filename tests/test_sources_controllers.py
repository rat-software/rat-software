"""
Unit tests for sources_controller_start.py and sources_controller_stop.py

sources_controller_start — SourcesController.start(workingdir)
    Spawns two threads: one runs job_sources.py, one runs job_reset_sources.py.

sources_controller_stop — SourcesController.stop(args)
    args[0]: list of browser process names to kill after a scraper process is found.
    Iterates psutil processes and kills those whose cmdline[1] matches one of five
    hard-coded script names.  Also kills browsers when a scraper process was found.
    Sleeps 60 s, then calls db.reset(job_server) from module scope.
    Swallows all exceptions per process.
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ── Shared path / libs stub ───────────────────────────────────────────────────
_SOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
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

sys.path.insert(0, _SOURCES_DIR)

import sources_controller_start as sc_start
import sources_controller_stop  as sc_stop

from sources_controller_start import SourcesController as StartController
from sources_controller_stop  import SourcesController as StopController


# ═════════════════════════════════════════════════════════════════════════════
# sources_controller_start
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesControllerStart(unittest.TestCase):

    # ── Thread creation ───────────────────────────────────────────────────────

    @patch('sources_controller_start.threading.Thread')
    def test_start_creates_exactly_two_threads(self, mock_thread):
        mock_thread.return_value = MagicMock()
        StartController().start('/work')
        self.assertEqual(mock_thread.call_count, 2)

    @patch('sources_controller_start.threading.Thread')
    def test_both_threads_are_started(self, mock_thread):
        instance = MagicMock()
        mock_thread.return_value = instance
        StartController().start('/work')
        self.assertEqual(instance.start.call_count, 2)

    @patch('sources_controller_start.threading.Thread')
    def test_thread_targets_are_callable(self, mock_thread):
        mock_thread.return_value = MagicMock()
        StartController().start('/work')
        for c in mock_thread.call_args_list:
            target = c[1].get('target') or c[0][0]
            self.assertTrue(callable(target))

    # ── Command content ───────────────────────────────────────────────────────

    def _capture_commands(self, workingdir='/work'):
        captured = []

        def capture_thread(target):
            captured.append(target)
            return MagicMock()

        with patch('sources_controller_start.threading.Thread',
                   side_effect=capture_thread), \
             patch('sources_controller_start.os.system') as mock_sys, \
             patch('builtins.print'):
            StartController().start(workingdir)
            for fn in captured:
                fn()

        return [c[0][0] for c in mock_sys.call_args_list]

    def test_job_sources_script_in_command(self):
        cmds = self._capture_commands()
        self.assertTrue(any('job_sources.py' in cmd for cmd in cmds))

    def test_job_reset_sources_script_in_command(self):
        cmds = self._capture_commands()
        self.assertTrue(any('job_reset_sources.py' in cmd for cmd in cmds))

    def test_commands_contain_workingdir(self):
        cmds = self._capture_commands('/my/workdir')
        for cmd in cmds:
            self.assertIn('/my/workdir', cmd)

    def test_commands_start_with_python(self):
        cmds = self._capture_commands()
        for cmd in cmds:
            self.assertTrue(cmd.startswith('python '))

    def test_two_distinct_commands_issued(self):
        cmds = self._capture_commands()
        self.assertEqual(len(set(cmds)), 2)

    def test_jobs_subdirectory_in_path(self):
        cmds = self._capture_commands()
        for cmd in cmds:
            self.assertIn('jobs', cmd)


# ═════════════════════════════════════════════════════════════════════════════
# sources_controller_stop — helpers
# ═════════════════════════════════════════════════════════════════════════════

def _make_proc(name='python3', cmdline=None):
    """Build a fake psutil process."""
    proc = MagicMock()
    proc.info = {
        'pid':     1234,
        'name':    name,
        'cmdline': cmdline if cmdline is not None else [],
    }
    return proc


def _run_stop(procs=None, browsers=None, db=None, job_server='srv'):
    """Patch dependencies and call StopController().stop(args)."""
    mock_db     = db or MagicMock()
    browser_list = browsers or []
    # inject db and job_server into module scope (they're referenced as free vars)
    with patch.object(sc_stop, 'db', mock_db, create=True), \
         patch.object(sc_stop, 'job_server', job_server, create=True), \
         patch('sources_controller_stop.psutil.process_iter',
               return_value=procs or []), \
         patch('sources_controller_stop.time.sleep'), \
         patch('builtins.print'):
        StopController().stop([browser_list])
    return mock_db


# ═════════════════════════════════════════════════════════════════════════════
# sources_controller_stop — process killing
# ═════════════════════════════════════════════════════════════════════════════

class TestSourcesControllerStop(unittest.TestCase):

    # ── Targeted scripts are killed ───────────────────────────────────────────

    def test_kills_job_sources_process(self):
        proc = _make_proc('python3', ['python3', 'job_sources.py'])
        _run_stop([proc])
        proc.kill.assert_called()

    def test_kills_sources_scraper_process(self):
        proc = _make_proc('python3', ['python3', 'sources_scraper.py'])
        _run_stop([proc])
        proc.kill.assert_called()

    def test_kills_sources_reset_process(self):
        proc = _make_proc('python3', ['python3', 'sources_reset.py'])
        _run_stop([proc])
        proc.kill.assert_called()

    def test_kills_job_reset_sources_process(self):
        proc = _make_proc('python3', ['python3', 'job_reset_sources.py'])
        _run_stop([proc])
        proc.kill.assert_called()

    def test_kills_controller_start_process(self):
        proc = _make_proc('python3', ['python3', 'sources_controller_start.py'])
        _run_stop([proc])
        proc.kill.assert_called()

    # ── Unrelated processes left alone ────────────────────────────────────────

    def test_does_not_kill_unrelated_python_process(self):
        # cmdline[1] doesn't match any kill-list name, and name is not in cmdline
        proc = _make_proc('python3', ['python3', 'my_other_app.py'])
        _run_stop([proc])
        proc.kill.assert_not_called()

    def test_does_not_kill_non_python_process(self):
        proc = _make_proc('nginx', ['nginx', '-g', 'daemon off;'])
        _run_stop([proc])
        proc.kill.assert_not_called()

    # ── Browser killing ───────────────────────────────────────────────────────

    def test_kills_browser_when_scraper_process_found(self):
        scraper = _make_proc('python3', ['python3', 'sources_scraper.py'])
        browser = _make_proc('chromium', ['chromium'])
        _run_stop([scraper, browser], browsers=['chromium'])
        browser.kill.assert_called()

    def test_does_not_kill_browser_without_scraper_process(self):
        # No python scraper proc found → kill_browser stays False
        browser = _make_proc('chromium', ['chromium'])
        _run_stop([browser], browsers=['chromium'])
        browser.kill.assert_not_called()

    # ── Exception handling ────────────────────────────────────────────────────

    def test_exception_on_kill_does_not_crash(self):
        proc = _make_proc('python3', ['python3', 'job_sources.py'])
        proc.kill.side_effect = Exception('access denied')
        try:
            _run_stop([proc])
        except Exception:
            self.fail('stop() should swallow per-process exceptions')

    def test_short_cmdline_does_not_crash(self):
        # cmdline with only one element → cmdline[1] raises IndexError → caught
        proc = _make_proc('python3', ['python3'])
        try:
            _run_stop([proc])
        except Exception:
            self.fail('stop() should handle short cmdline gracefully')

    def test_none_cmdline_does_not_crash(self):
        proc = _make_proc('python3')
        proc.info['cmdline'] = None
        try:
            _run_stop([proc])
        except Exception:
            self.fail('stop() should handle None cmdline gracefully')

    # ── Post-loop actions ─────────────────────────────────────────────────────

    def test_sleep_called_with_60(self):
        with patch.object(sc_stop, 'db', MagicMock(), create=True), \
             patch.object(sc_stop, 'job_server', 'srv', create=True), \
             patch('sources_controller_stop.psutil.process_iter', return_value=[]), \
             patch('sources_controller_stop.time.sleep') as mock_sleep, \
             patch('builtins.print'):
            StopController().stop([[]])
        mock_sleep.assert_called_once_with(60)

    def test_db_reset_called_after_sleep(self):
        call_order = []
        mock_db = MagicMock()
        mock_db.reset.side_effect = lambda *a: call_order.append('db.reset')

        with patch.object(sc_stop, 'db', mock_db, create=True), \
             patch.object(sc_stop, 'job_server', 'srv', create=True), \
             patch('sources_controller_stop.psutil.process_iter', return_value=[]), \
             patch('sources_controller_stop.time.sleep',
                   side_effect=lambda *a: call_order.append('sleep')), \
             patch('builtins.print'):
            StopController().stop([[]])

        self.assertEqual(call_order, ['sleep', 'db.reset'])

    def test_db_reset_called_with_job_server(self):
        mock_db = MagicMock()
        with patch.object(sc_stop, 'db', mock_db, create=True), \
             patch.object(sc_stop, 'job_server', 'my-server', create=True), \
             patch('sources_controller_stop.psutil.process_iter', return_value=[]), \
             patch('sources_controller_stop.time.sleep'), \
             patch('builtins.print'):
            StopController().stop([[]])
        mock_db.reset.assert_called_once_with('my-server')


if __name__ == '__main__':
    unittest.main()
