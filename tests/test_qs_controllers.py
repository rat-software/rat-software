"""
Unit tests for query_sampler_controller_start.py and query_sampler_controller_stop.py

query_sampler_controller_start — KeywordController.start(workingdir)
    Spawns two threads: one for job_qs.py, one for job_reset_qs.py.

query_sampler_controller_stop — KeywordController.stop()
    Iterates psutil processes and kills those whose command line matches one
    of five hard-coded script names.  Swallows psutil-specific exceptions per
    process so one dead process cannot abort the whole sweep.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

# ── Path setup ────────────────────────────────────────────────────────────────
_QS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'query_sampler',
)
sys.path.insert(0, _QS_DIR)

from query_sampler_controller_start import KeywordController as StartController
from query_sampler_controller_stop  import KeywordController as StopController


# ═════════════════════════════════════════════════════════════════════════════
# query_sampler_controller_start
# ═════════════════════════════════════════════════════════════════════════════

class TestQuerySamplerControllerStart(unittest.TestCase):

    # ── Thread creation ───────────────────────────────────────────────────────

    @patch('query_sampler_controller_start.threading.Thread')
    def test_start_creates_exactly_two_threads(self, mock_thread):
        mock_thread.return_value = MagicMock()
        StartController().start('/some/dir')
        self.assertEqual(mock_thread.call_count, 2)

    @patch('query_sampler_controller_start.threading.Thread')
    def test_both_threads_are_started(self, mock_thread):
        instance = MagicMock()
        mock_thread.return_value = instance
        StartController().start('/some/dir')
        self.assertEqual(instance.start.call_count, 2)

    @patch('query_sampler_controller_start.threading.Thread')
    def test_thread_targets_are_callable(self, mock_thread):
        mock_thread.return_value = MagicMock()
        StartController().start('/some/dir')
        for c in mock_thread.call_args_list:
            target = c[1].get('target') or c[0][0]
            self.assertTrue(callable(target))

    # ── Command content ───────────────────────────────────────────────────────

    def _capture_commands(self, workingdir):
        """Run start() and return the list of os.system commands issued."""
        captured_fns = []

        def capture_thread(target):
            captured_fns.append(target)
            return MagicMock()

        with patch('query_sampler_controller_start.threading.Thread',
                   side_effect=capture_thread), \
             patch('query_sampler_controller_start.os.system') as mock_sys, \
             patch('builtins.print'):
            StartController().start(workingdir)
            for fn in captured_fns:
                fn()

        return [c[0][0] for c in mock_sys.call_args_list]

    def test_job_qs_script_referenced_in_command(self):
        cmds = self._capture_commands('/work')
        self.assertTrue(any('job_qs.py' in cmd for cmd in cmds))

    def test_job_reset_qs_script_referenced_in_command(self):
        cmds = self._capture_commands('/work')
        self.assertTrue(any('job_reset_qs.py' in cmd for cmd in cmds))

    def test_commands_contain_workingdir(self):
        cmds = self._capture_commands('/my/workdir')
        for cmd in cmds:
            self.assertIn('/my/workdir', cmd)

    def test_commands_start_with_python(self):
        cmds = self._capture_commands('/work')
        for cmd in cmds:
            self.assertTrue(cmd.startswith('python '))

    def test_two_distinct_commands_issued(self):
        cmds = self._capture_commands('/work')
        self.assertEqual(len(set(cmds)), 2, 'Expected two distinct os.system calls')

    def test_jobs_subdirectory_included_in_path(self):
        cmds = self._capture_commands('/work')
        for cmd in cmds:
            self.assertIn('jobs', cmd)


# ═════════════════════════════════════════════════════════════════════════════
# query_sampler_controller_stop — helpers
# ═════════════════════════════════════════════════════════════════════════════

def _make_proc(name='python3', cmdline=None, exc_on_kill=None):
    """Build a fake psutil process object."""
    proc = MagicMock()
    proc.info = {'pid': 1234, 'name': name, 'cmdline': cmdline or []}
    if exc_on_kill:
        proc.kill.side_effect = exc_on_kill
    return proc


def _run_stop(procs=None):
    """Patch psutil.process_iter and call stop(); return the proc list."""
    procs = procs or []
    with patch('query_sampler_controller_stop.psutil.process_iter',
               return_value=procs), \
         patch('builtins.print'):
        StopController().stop()
    return procs


# ═════════════════════════════════════════════════════════════════════════════
# query_sampler_controller_stop — process killing
# ═════════════════════════════════════════════════════════════════════════════

class TestQuerySamplerControllerStop(unittest.TestCase):

    # ── Targeted processes are killed ─────────────────────────────────────────

    def test_kills_job_qs_process(self):
        proc = _make_proc('python3', ['python3', 'job_qs.py'])
        _run_stop([proc])
        proc.kill.assert_called_once()

    def test_kills_generate_keywords_process(self):
        proc = _make_proc('python3', ['python3', 'generate_keywords.py'])
        _run_stop([proc])
        proc.kill.assert_called_once()

    def test_kills_controller_start_process(self):
        proc = _make_proc('python3', ['python3', 'query_sampler_controller_start.py'])
        _run_stop([proc])
        proc.kill.assert_called_once()

    def test_kills_job_reset_qs_process(self):
        proc = _make_proc('python3', ['python3', 'job_reset_qs.py'])
        _run_stop([proc])
        proc.kill.assert_called_once()

    def test_kills_qs_reset_process(self):
        proc = _make_proc('python3', ['python3', 'qs_reset.py'])
        _run_stop([proc])
        proc.kill.assert_called_once()

    def test_kills_multiple_matching_processes(self):
        proc1 = _make_proc('python3', ['python3', 'job_qs.py'])
        proc2 = _make_proc('python3', ['python3', 'job_reset_qs.py'])
        _run_stop([proc1, proc2])
        proc1.kill.assert_called_once()
        proc2.kill.assert_called_once()

    # ── Unrelated processes are left alone ────────────────────────────────────

    def test_does_not_kill_unrelated_python_process(self):
        proc = _make_proc('python3', ['python3', 'my_other_script.py'])
        _run_stop([proc])
        proc.kill.assert_not_called()

    def test_does_not_kill_non_python_process(self):
        proc = _make_proc('nginx', ['nginx', '-g', 'daemon off;'])
        _run_stop([proc])
        proc.kill.assert_not_called()

    def test_does_not_kill_empty_cmdline_process(self):
        proc = _make_proc('python3', cmdline=[])
        _run_stop([proc])
        proc.kill.assert_not_called()

    # ── psutil exception handling ─────────────────────────────────────────────

    def test_no_such_process_does_not_crash(self):
        import psutil
        proc = _make_proc('python3', ['python3', 'job_qs.py'],
                          exc_on_kill=psutil.NoSuchProcess(pid=1234))
        try:
            _run_stop([proc])
        except psutil.NoSuchProcess:
            self.fail('stop() should swallow NoSuchProcess')

    def test_access_denied_does_not_crash(self):
        import psutil
        proc = _make_proc('python3', ['python3', 'job_qs.py'],
                          exc_on_kill=psutil.AccessDenied(pid=1234))
        try:
            _run_stop([proc])
        except psutil.AccessDenied:
            self.fail('stop() should swallow AccessDenied')

    def test_zombie_process_does_not_crash(self):
        import psutil
        proc = _make_proc('python3', ['python3', 'job_qs.py'],
                          exc_on_kill=psutil.ZombieProcess(pid=1234))
        try:
            _run_stop([proc])
        except psutil.ZombieProcess:
            self.fail('stop() should swallow ZombieProcess')

    def test_none_cmdline_does_not_crash(self):
        proc = _make_proc('python3')
        proc.info['cmdline'] = None
        try:
            _run_stop([proc])
        except Exception:
            self.fail('stop() should handle None cmdline gracefully')

    # ── Kill-list completeness ────────────────────────────────────────────────

    def test_all_five_target_scripts_are_in_kill_list(self):
        """Verify the hard-coded kill list matches the expected scripts."""
        expected = {
            'job_qs.py',
            'generate_keywords.py',
            'query_sampler_controller_start.py',
            'job_reset_qs.py',
            'qs_reset.py',
        }
        killed = set()
        procs = [_make_proc('python3', ['python3', name]) for name in expected]
        _run_stop(procs)
        for proc, name in zip(procs, expected):
            if proc.kill.called:
                killed.add(name)
        self.assertEqual(killed, expected)


if __name__ == '__main__':
    unittest.main()
