"""
Unit tests for job_qs.py and job_reset_qs.py

job_qs.py — job()
    Determines the working directory (parent dir when "jobs" is in the path,
    otherwise current dir) and runs generate_keywords.py via os.system.

job_reset_qs.py — job()
    Same path logic as job_qs.job(), but runs query_sampler_reset.py instead.
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Path setup ────────────────────────────────────────────────────────────────
_JOBS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'query_sampler', 'jobs',
)
sys.path.insert(0, _JOBS_DIR)

# Stub apscheduler so the modules can be imported without the package installed.
_apscheduler = types.ModuleType('apscheduler')
_apscheduler.__path__ = []
_apscheduler_schedulers = types.ModuleType('apscheduler.schedulers')
_apscheduler_schedulers.__path__ = []
_apscheduler_schedulers_bg = types.ModuleType('apscheduler.schedulers.background')
_apscheduler_schedulers_bg.BackgroundScheduler = type('BackgroundScheduler', (), {})

sys.modules.setdefault('apscheduler', _apscheduler)
sys.modules.setdefault('apscheduler.schedulers', _apscheduler_schedulers)
sys.modules.setdefault('apscheduler.schedulers.background', _apscheduler_schedulers_bg)

import job_qs
import job_reset_qs


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _run_job(module, fake_file_path):
    """
    Invoke module.job() with a controlled file path and capture os.system.

    fake_file_path should be an absolute path such as
    '/some/path/jobs/job_qs.py' (with "jobs" in the path) or
    '/some/other/dir/job_qs.py' (without "jobs") to exercise both branches.
    """
    with patch.object(module.inspect, 'currentframe', return_value=MagicMock()), \
         patch.object(module.inspect, 'getfile', return_value=fake_file_path), \
         patch.object(module.os.path, 'abspath', return_value=fake_file_path), \
         patch.object(module.os, 'system') as mock_system:
        module.job()
    return mock_system


# ═════════════════════════════════════════════════════════════════════════════
# job_qs — job_defaults
# ═════════════════════════════════════════════════════════════════════════════

class TestJobQsDefaults(unittest.TestCase):

    def test_max_instances_is_two(self):
        self.assertEqual(job_qs.job_defaults['max_instances'], 2)

    def test_job_defaults_is_dict(self):
        self.assertIsInstance(job_qs.job_defaults, dict)


# ═════════════════════════════════════════════════════════════════════════════
# job_qs — job()
# ═════════════════════════════════════════════════════════════════════════════

class TestJobQsJob(unittest.TestCase):

    # ── os.system call ────────────────────────────────────────────────────────

    def test_os_system_called_once(self):
        mock_system = _run_job(job_qs, '/some/path/jobs/job_qs.py')
        mock_system.assert_called_once()

    def test_command_starts_with_python(self):
        mock_system = _run_job(job_qs, '/some/path/jobs/job_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertTrue(cmd.startswith('python '))

    def test_command_targets_generate_keywords(self):
        mock_system = _run_job(job_qs, '/some/path/jobs/job_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertIn('generate_keywords.py', cmd)

    # ── Working-directory logic ───────────────────────────────────────────────

    def test_workingdir_is_parent_when_jobs_in_currentdir(self):
        # /some/path/jobs → "jobs" in path → workingdir = /some/path
        mock_system = _run_job(job_qs, '/some/path/jobs/job_qs.py')
        cmd = mock_system.call_args[0][0]
        expected_script = os.path.join('/some/path', 'generate_keywords.py')
        self.assertIn(expected_script, cmd)

    def test_workingdir_is_not_jobs_dir_when_jobs_in_currentdir(self):
        # The "jobs" directory itself must not appear in the script path.
        mock_system = _run_job(job_qs, '/some/path/jobs/job_qs.py')
        cmd = mock_system.call_args[0][0]
        wrong_path = os.path.join('/some/path/jobs', 'generate_keywords.py')
        self.assertNotIn(wrong_path, cmd)

    def test_workingdir_is_currentdir_when_jobs_not_in_path(self):
        # /some/other/dir → "jobs" not in path → workingdir = /some/other/dir
        mock_system = _run_job(job_qs, '/some/other/dir/job_qs.py')
        cmd = mock_system.call_args[0][0]
        expected_script = os.path.join('/some/other/dir', 'generate_keywords.py')
        self.assertIn(expected_script, cmd)

    def test_command_is_a_string(self):
        mock_system = _run_job(job_qs, '/some/path/jobs/job_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertIsInstance(cmd, str)


# ═════════════════════════════════════════════════════════════════════════════
# job_reset_qs — job_defaults
# ═════════════════════════════════════════════════════════════════════════════

class TestJobResetQsDefaults(unittest.TestCase):

    def test_max_instances_is_one(self):
        self.assertEqual(job_reset_qs.job_defaults['max_instances'], 1)

    def test_job_defaults_is_dict(self):
        self.assertIsInstance(job_reset_qs.job_defaults, dict)

    def test_max_instances_differs_from_job_qs(self):
        # job_reset_qs intentionally allows fewer concurrent instances.
        self.assertNotEqual(
            job_reset_qs.job_defaults['max_instances'],
            job_qs.job_defaults['max_instances'],
        )


# ═════════════════════════════════════════════════════════════════════════════
# job_reset_qs — job()
# ═════════════════════════════════════════════════════════════════════════════

class TestJobResetQsJob(unittest.TestCase):

    # ── os.system call ────────────────────────────────────────────────────────

    def test_os_system_called_once(self):
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        mock_system.assert_called_once()

    def test_command_starts_with_python(self):
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertTrue(cmd.startswith('python '))

    def test_command_targets_query_sampler_reset(self):
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertIn('query_sampler_reset.py', cmd)

    # ── Working-directory logic ───────────────────────────────────────────────

    def test_workingdir_is_parent_when_jobs_in_currentdir(self):
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        expected_script = os.path.join('/some/path', 'query_sampler_reset.py')
        self.assertIn(expected_script, cmd)

    def test_workingdir_is_not_jobs_dir_when_jobs_in_currentdir(self):
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        wrong_path = os.path.join('/some/path/jobs', 'query_sampler_reset.py')
        self.assertNotIn(wrong_path, cmd)

    def test_workingdir_is_currentdir_when_jobs_not_in_path(self):
        mock_system = _run_job(job_reset_qs, '/some/other/dir/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        expected_script = os.path.join('/some/other/dir', 'query_sampler_reset.py')
        self.assertIn(expected_script, cmd)

    def test_command_is_a_string(self):
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertIsInstance(cmd, str)

    def test_does_not_run_generate_keywords(self):
        # Ensure the reset job does not accidentally invoke the wrong script.
        mock_system = _run_job(job_reset_qs, '/some/path/jobs/job_reset_qs.py')
        cmd = mock_system.call_args[0][0]
        self.assertNotIn('generate_keywords.py', cmd)


if __name__ == '__main__':
    unittest.main()
