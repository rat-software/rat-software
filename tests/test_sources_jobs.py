"""
Unit tests for rat-backend/sources/jobs/job_sources.py
                and rat-backend/sources/jobs/job_reset_sources.py

job_sources.py — job()
    Determines the working directory and runs sources_scraper.py via os.system.
    job_defaults['max_instances'] == 2.

job_reset_sources.py — job()
    Same path logic, but runs sources_reset.py instead.
    job_defaults['max_instances'] == 1.
"""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Paths ──────────────────────────────────────────────────────────────────────
_JOBS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'rat-backend', 'sources', 'jobs',
)
_SOURCES_DIR = os.path.dirname(_JOBS_DIR)

# ── Stubs — must be in sys.modules before importing ───────────────────────────

# apscheduler
_apscheduler = types.ModuleType('apscheduler')
_apscheduler.__path__ = []
_apscheduler_schedulers = types.ModuleType('apscheduler.schedulers')
_apscheduler_schedulers.__path__ = []
_apscheduler_schedulers_bg = types.ModuleType('apscheduler.schedulers.background')
_apscheduler_schedulers_bg.BackgroundScheduler = type('BackgroundScheduler', (), {})
sys.modules.setdefault('apscheduler',                        _apscheduler)
sys.modules.setdefault('apscheduler.schedulers',             _apscheduler_schedulers)
sys.modules.setdefault('apscheduler.schedulers.background',  _apscheduler_schedulers_bg)

# libs.lib_logger  (job_sources / job_reset_sources do `from libs.lib_logger import *`)
_libs_pkg = types.ModuleType('libs')
_libs_pkg.__path__ = [os.path.join(_SOURCES_DIR, 'libs')]
sys.modules.setdefault('libs', _libs_pkg)

_lib_logger_stub = types.ModuleType('libs.lib_logger')
_lib_logger_stub.Logger = type('Logger', (), {})
sys.modules.setdefault('libs.lib_logger', _lib_logger_stub)
setattr(_libs_pkg, 'lib_logger', _lib_logger_stub)

# ── Load modules ───────────────────────────────────────────────────────────────

def _load(filename, modname):
    spec = importlib.util.spec_from_file_location(
        modname, os.path.join(_JOBS_DIR, filename)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[modname] = mod
    return mod

job_sources       = _load('job_sources.py',       'job_sources')
job_reset_sources = _load('job_reset_sources.py',  'job_reset_sources')


# ── Helper ────────────────────────────────────────────────────────────────────

def _run_job(module, fake_file_path):
    """
    Call module.job() with a controlled file path; return the captured
    os.system mock so callers can inspect the issued command.
    """
    with patch.object(module.inspect, 'currentframe', return_value=MagicMock()), \
         patch.object(module.inspect, 'getfile',      return_value=fake_file_path), \
         patch.object(module.os.path, 'abspath',      return_value=fake_file_path), \
         patch.object(module.os,      'system') as mock_sys:
        module.job()
    return mock_sys


# ═════════════════════════════════════════════════════════════════════════════
# job_sources — job_defaults
# ═════════════════════════════════════════════════════════════════════════════

class TestJobSourcesDefaults(unittest.TestCase):

    def test_max_instances_is_two(self):
        self.assertEqual(job_sources.job_defaults['max_instances'], 2)

    def test_job_defaults_is_dict(self):
        self.assertIsInstance(job_sources.job_defaults, dict)


# ═════════════════════════════════════════════════════════════════════════════
# job_sources — job()
# ═════════════════════════════════════════════════════════════════════════════

class TestJobSourcesJob(unittest.TestCase):

    def test_os_system_called_once(self):
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        mock_sys.assert_called_once()

    def test_command_starts_with_python(self):
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        self.assertTrue(mock_sys.call_args[0][0].startswith('python '))

    def test_command_targets_sources_scraper(self):
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        self.assertIn('sources_scraper.py', mock_sys.call_args[0][0])

    def test_workingdir_is_parent_when_jobs_in_currentdir(self):
        # /some/path/jobs → workingdir = /some/path
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        cmd = mock_sys.call_args[0][0]
        self.assertIn('/some/path', cmd)

    def test_workingdir_is_not_jobs_dir_when_jobs_in_currentdir(self):
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        cmd = mock_sys.call_args[0][0]
        # Must NOT reference the jobs/ subdir as the base
        self.assertNotIn('/some/path/jobs/sources_scraper.py', cmd)

    def test_workingdir_is_currentdir_when_jobs_not_in_path(self):
        # /some/other/dir → workingdir = /some/other/dir
        mock_sys = _run_job(job_sources, '/some/other/dir/job_sources.py')
        cmd = mock_sys.call_args[0][0]
        self.assertIn('/some/other/dir', cmd)

    def test_command_is_a_string(self):
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        self.assertIsInstance(mock_sys.call_args[0][0], str)

    def test_does_not_reference_reset_script(self):
        mock_sys = _run_job(job_sources, '/some/path/jobs/job_sources.py')
        self.assertNotIn('sources_reset.py', mock_sys.call_args[0][0])


# ═════════════════════════════════════════════════════════════════════════════
# job_reset_sources — job_defaults
# ═════════════════════════════════════════════════════════════════════════════

class TestJobResetSourcesDefaults(unittest.TestCase):

    def test_max_instances_is_one(self):
        self.assertEqual(job_reset_sources.job_defaults['max_instances'], 1)

    def test_job_defaults_is_dict(self):
        self.assertIsInstance(job_reset_sources.job_defaults, dict)

    def test_max_instances_differs_from_job_sources(self):
        self.assertNotEqual(
            job_reset_sources.job_defaults['max_instances'],
            job_sources.job_defaults['max_instances'],
        )


# ═════════════════════════════════════════════════════════════════════════════
# job_reset_sources — job()
# ═════════════════════════════════════════════════════════════════════════════

class TestJobResetSourcesJob(unittest.TestCase):

    def test_os_system_called_once(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        mock_sys.assert_called_once()

    def test_command_starts_with_python(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        self.assertTrue(mock_sys.call_args[0][0].startswith('python '))

    def test_command_targets_sources_reset(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        self.assertIn('sources_reset.py', mock_sys.call_args[0][0])

    def test_workingdir_is_parent_when_jobs_in_currentdir(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        cmd = mock_sys.call_args[0][0]
        self.assertIn('/some/path', cmd)

    def test_workingdir_is_not_jobs_dir_when_jobs_in_currentdir(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        cmd = mock_sys.call_args[0][0]
        self.assertNotIn('/some/path/jobs/sources_reset.py', cmd)

    def test_workingdir_is_currentdir_when_jobs_not_in_path(self):
        mock_sys = _run_job(job_reset_sources, '/some/other/dir/job_reset_sources.py')
        cmd = mock_sys.call_args[0][0]
        self.assertIn('/some/other/dir', cmd)

    def test_command_is_a_string(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        self.assertIsInstance(mock_sys.call_args[0][0], str)

    def test_does_not_reference_scraper_script(self):
        mock_sys = _run_job(job_reset_sources, '/some/path/jobs/job_reset_sources.py')
        self.assertNotIn('sources_scraper.py', mock_sys.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
