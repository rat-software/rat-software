"""
Unit tests for rat-storage/clean_orphans.py

Covers:
  - Early exit when STORAGE_FOLDER does not exist (no DB call)
  - Early exit on DB connection error (no disk scan)
  - DB errors do not propagate as exceptions
  - Clean state: all files registered → no deletion prompt
  - Empty storage directory → no deletion prompt
  - Dot-files (.DS_Store, .gitignore, …) are never treated as orphans
  - Dot-file mixed with a real orphan: prompt fires for the real one only
  - Case-insensitive filename matching (physical vs DB)
  - Decline ('n') → orphan preserved on disk
  - Confirm ('y') → orphan removed, registered files kept
  - Multiple orphans: all removed on confirm
  - Files referenced in both serp and source tables are not orphaned
  - os.remove failure is silently skipped (no exception raised)
"""
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# ── Load module ───────────────────────────────────────────────────────────────
_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'rat-storage', 'clean_orphans.py',
)
_spec = importlib.util.spec_from_file_location('clean_orphans', _LIB_PATH)
_mod  = importlib.util.module_from_spec(_spec)
sys.modules['clean_orphans'] = _mod
_spec.loader.exec_module(_mod)


# ── Shared helpers ────────────────────────────────────────────────────────────

class _Base(unittest.TestCase):
    """Temp storage dir + safe module-global overrides before every test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        _mod.STORAGE_FOLDER = self.tmpdir
        _mod.DB_URI = 'postgresql://fake'

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, *filenames):
        for f in filenames:
            with open(os.path.join(self.tmpdir, f), 'w'):
                pass

    def _db_mock(self, serp=(), source=()):
        """
        Build a create_engine mock whose connection yields the given file lists.
        First conn.execute() call returns serp rows; second returns source rows.
        """
        eng  = MagicMock()
        conn = MagicMock()
        eng.connect.return_value.__enter__.return_value = conn
        conn.execute.side_effect = [
            [(f,) for f in serp],
            [(f,) for f in source],
        ]
        return eng


# ─────────────────────────────────────────────────────────────────────────────
# Early-exit: missing storage folder
# ─────────────────────────────────────────────────────────────────────────────

class TestMissingStorageFolder(_Base):

    def test_returns_without_calling_db(self):
        _mod.STORAGE_FOLDER = '/nonexistent/xyz_rat_test'
        with patch.object(_mod, 'create_engine') as mock_create:
            _mod.clean_orphans()
            mock_create.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Early-exit: database error
# ─────────────────────────────────────────────────────────────────────────────

class TestDBError(_Base):

    def _failing_engine(self, exc=Exception('db error')):
        eng = MagicMock()
        eng.connect.side_effect = exc
        return eng

    def test_db_error_returns_without_scanning_disk(self):
        with patch.object(_mod, 'create_engine', return_value=self._failing_engine()):
            with patch('os.listdir') as mock_ls:
                _mod.clean_orphans()
                mock_ls.assert_not_called()

    def test_db_error_does_not_propagate(self):
        with patch.object(_mod, 'create_engine', return_value=self._failing_engine(RuntimeError('timeout'))):
            _mod.clean_orphans()  # must not raise

    def test_db_error_does_not_prompt_user(self):
        with patch.object(_mod, 'create_engine', return_value=self._failing_engine()):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Clean state — no orphans
# ─────────────────────────────────────────────────────────────────────────────

class TestNoOrphans(_Base):

    def test_all_files_in_db_no_prompt(self):
        self._write('a.zip', 'b.zip')
        eng = self._db_mock(serp=['a.zip'], source=['b.zip'])
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()

    def test_empty_directory_no_prompt(self):
        eng = self._db_mock()
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Dot-file filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestDotFilesSkipped(_Base):

    def test_dot_files_alone_cause_no_prompt(self):
        self._write('.DS_Store', '.gitignore')
        eng = self._db_mock()  # DB empty — but dot-files must be ignored
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()

    def test_dot_file_mixed_with_real_orphan_prompts_once(self):
        self._write('.DS_Store', 'orphan.zip')
        eng = self._db_mock()  # neither file in DB, but .DS_Store ignored
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='n') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_called_once()  # exactly one real orphan


# ─────────────────────────────────────────────────────────────────────────────
# Case-insensitive matching
# ─────────────────────────────────────────────────────────────────────────────

class TestCaseInsensitiveMatching(_Base):

    def test_uppercase_physical_matches_lowercase_db(self):
        self._write('REPORT.ZIP')
        eng = self._db_mock(serp=['report.zip'])
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()

    def test_mixed_case_physical_matches_db(self):
        self._write('Page_001.Zip')
        eng = self._db_mock(source=['page_001.zip'])
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()

    def test_uppercase_db_entry_matches_lowercase_physical(self):
        self._write('file.zip')
        eng = self._db_mock(serp=['FILE.ZIP'])
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input') as mock_input:
                _mod.clean_orphans()
                mock_input.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Orphan deletion behaviour
# ─────────────────────────────────────────────────────────────────────────────

class TestOrphanDeletion(_Base):

    def test_decline_preserves_orphan_on_disk(self):
        self._write('orphan.zip')
        eng = self._db_mock()
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='n'):
                _mod.clean_orphans()
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'orphan.zip')))

    def test_confirm_removes_orphan_from_disk(self):
        self._write('orphan.zip')
        eng = self._db_mock()
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='y'):
                _mod.clean_orphans()
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, 'orphan.zip')))

    def test_confirm_keeps_registered_files_intact(self):
        self._write('registered.zip', 'orphan.zip')
        eng = self._db_mock(serp=['registered.zip'])
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='y'):
                _mod.clean_orphans()
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'registered.zip')))
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, 'orphan.zip')))

    def test_multiple_orphans_all_deleted_on_confirm(self):
        self._write('a.zip', 'b.zip', 'c.zip')
        eng = self._db_mock()
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='y'):
                _mod.clean_orphans()
        for f in ('a.zip', 'b.zip', 'c.zip'):
            self.assertFalse(os.path.exists(os.path.join(self.tmpdir, f)))

    def test_files_in_both_serp_and_source_not_orphaned(self):
        self._write('serp.zip', 'source.zip', 'orphan.zip')
        eng = self._db_mock(serp=['serp.zip'], source=['source.zip'])
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='y'):
                _mod.clean_orphans()
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'serp.zip')))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'source.zip')))
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, 'orphan.zip')))

    def test_remove_failure_silently_skipped(self):
        self._write('orphan.zip')
        eng = self._db_mock()
        with patch.object(_mod, 'create_engine', return_value=eng):
            with patch('builtins.input', return_value='y'):
                with patch('os.remove', side_effect=PermissionError('denied')):
                    _mod.clean_orphans()  # must not propagate


if __name__ == '__main__':
    unittest.main()
