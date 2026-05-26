"""
Unit tests for classifier.py (Classifier.load_classifier)
         and classifier_reset.py (ClassifierReset.__init__ / .reset)
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

# Stub `libs` package so "from libs.lib_helper import Helper" etc. work
# without a live database.
_libs_pkg = sys.modules.get('libs') or types.ModuleType('libs')
_libs_pkg.__path__ = [os.path.join(_CLASSIFIER_DIR, 'libs')]
sys.modules.setdefault('libs', _libs_pkg)

for _stub_name, _attr in [('libs.lib_helper', 'Helper'), ('libs.lib_db', 'DB')]:
    if _stub_name not in sys.modules:
        _m = types.ModuleType(_stub_name)
        setattr(_m, _attr, type(_attr, (), {}))
        sys.modules[_stub_name] = _m
        setattr(_libs_pkg, _stub_name.split('.')[-1], _m)

from classifier       import Classifier
from classifier_reset import ClassifierReset


# ═════════════════════════════════════════════════════════════════════════════
# ClassifierReset
# ═════════════════════════════════════════════════════════════════════════════

class TestClassifierResetInit(unittest.TestCase):

    def test_db_stored_as_instance_attribute(self):
        db = MagicMock()
        cr = ClassifierReset(db)
        self.assertIs(cr.db, db)

    def test_accepts_any_db_object(self):
        for db in (MagicMock(), object(), {'key': 'val'}):
            cr = ClassifierReset(db)
            self.assertIs(cr.db, db)


class TestClassifierResetReset(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.cr = ClassifierReset(self.db)

    def test_reset_calls_db_reset(self):
        self.cr.reset('server1')
        self.db.reset.assert_called_once()

    def test_reset_passes_job_server_argument(self):
        self.cr.reset('my_job_server')
        self.db.reset.assert_called_once_with('my_job_server')

    def test_reset_with_different_job_server_values(self):
        for server in ('server_a', 'server_b', 'prod'):
            db = MagicMock()
            ClassifierReset(db).reset(server)
            db.reset.assert_called_once_with(server)

    def test_reset_called_exactly_once_per_invocation(self):
        self.cr.reset('srv')
        self.assertEqual(self.db.reset.call_count, 1)

    def test_multiple_resets_each_call_db_reset(self):
        self.cr.reset('srv1')
        self.cr.reset('srv2')
        self.assertEqual(self.db.reset.call_count, 2)
        self.db.reset.assert_any_call('srv1')
        self.db.reset.assert_any_call('srv2')


# ═════════════════════════════════════════════════════════════════════════════
# Classifier.load_classifier
# ═════════════════════════════════════════════════════════════════════════════

def _make_classifier(name='seo_score', cid=1, study=10):
    return {'name': name, 'id': cid, 'study': study}


class TestLoadClassifierImport(unittest.TestCase):
    """Verifies that import_module is called with the right module path."""

    @patch('classifier.importlib.import_module')
    def test_empty_list_causes_no_imports(self, mock_import):
        Classifier().load_classifier([], MagicMock(), MagicMock(), 'srv')
        mock_import.assert_not_called()

    @patch('classifier.importlib.import_module')
    def test_single_classifier_imports_correct_module(self, mock_import):
        mock_import.return_value = MagicMock()
        Classifier().load_classifier(
            [_make_classifier('seo_score')], MagicMock(), MagicMock(), 'srv'
        )
        mock_import.assert_called_once_with('classifiers.seo_score.seo_score')

    @patch('classifier.importlib.import_module')
    def test_module_path_uses_classifier_name_twice(self, mock_import):
        mock_import.return_value = MagicMock()
        Classifier().load_classifier(
            [_make_classifier('readability_score')], MagicMock(), MagicMock(), 'srv'
        )
        args = mock_import.call_args[0][0]
        self.assertEqual(args, 'classifiers.readability_score.readability_score')

    @patch('classifier.importlib.import_module')
    def test_multiple_classifiers_each_imported(self, mock_import):
        mock_import.return_value = MagicMock()
        classifiers = [
            _make_classifier('seo_score',        cid=1),
            _make_classifier('readability_score', cid=2),
            _make_classifier('seo_rule_based',    cid=3),
        ]
        Classifier().load_classifier(classifiers, MagicMock(), MagicMock(), 'srv')
        self.assertEqual(mock_import.call_count, 3)
        imported = [c[0][0] for c in mock_import.call_args_list]
        self.assertIn('classifiers.seo_score.seo_score',               imported)
        self.assertIn('classifiers.readability_score.readability_score', imported)
        self.assertIn('classifiers.seo_rule_based.seo_rule_based',      imported)


class TestLoadClassifierMainCall(unittest.TestCase):
    """Verifies that each imported module's main() is called correctly."""

    @patch('classifier.importlib.import_module')
    def test_main_called_with_classifier_id(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module
        db, helper = MagicMock(), MagicMock()

        Classifier().load_classifier([_make_classifier(cid=42)], db, helper, 'srv')

        args = fake_module.main.call_args[0]
        self.assertEqual(args[0], 42)

    @patch('classifier.importlib.import_module')
    def test_main_called_with_db(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module
        db, helper = MagicMock(), MagicMock()

        Classifier().load_classifier([_make_classifier()], db, helper, 'srv')

        args = fake_module.main.call_args[0]
        self.assertIs(args[1], db)

    @patch('classifier.importlib.import_module')
    def test_main_called_with_helper(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module
        db, helper = MagicMock(), MagicMock()

        Classifier().load_classifier([_make_classifier()], db, helper, 'srv')

        args = fake_module.main.call_args[0]
        self.assertIs(args[2], helper)

    @patch('classifier.importlib.import_module')
    def test_main_called_with_job_server(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module

        Classifier().load_classifier(
            [_make_classifier()], MagicMock(), MagicMock(), 'my_server'
        )

        args = fake_module.main.call_args[0]
        self.assertEqual(args[3], 'my_server')

    @patch('classifier.importlib.import_module')
    def test_main_called_with_study_id(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module

        Classifier().load_classifier(
            [_make_classifier(study=99)], MagicMock(), MagicMock(), 'srv'
        )

        args = fake_module.main.call_args[0]
        self.assertEqual(args[4], 99)

    @patch('classifier.importlib.import_module')
    def test_main_called_exactly_once_per_classifier(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module

        Classifier().load_classifier(
            [_make_classifier(cid=1), _make_classifier(cid=2)],
            MagicMock(), MagicMock(), 'srv'
        )
        self.assertEqual(fake_module.main.call_count, 2)

    @patch('classifier.importlib.import_module')
    def test_each_classifier_gets_its_own_id_and_study(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module

        classifiers = [
            _make_classifier('seo_score',        cid=10, study=1),
            _make_classifier('readability_score', cid=20, study=2),
        ]
        Classifier().load_classifier(classifiers, MagicMock(), MagicMock(), 'srv')

        calls = fake_module.main.call_args_list
        self.assertEqual(calls[0][0][0], 10)
        self.assertEqual(calls[0][0][4], 1)
        self.assertEqual(calls[1][0][0], 20)
        self.assertEqual(calls[1][0][4], 2)

    @patch('classifier.importlib.import_module')
    def test_db_and_helper_same_object_for_all_classifiers(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module
        db, helper = MagicMock(), MagicMock()

        classifiers = [_make_classifier(cid=1), _make_classifier(cid=2)]
        Classifier().load_classifier(classifiers, db, helper, 'srv')

        for c in fake_module.main.call_args_list:
            self.assertIs(c[0][1], db)
            self.assertIs(c[0][2], helper)

    @patch('classifier.importlib.import_module')
    def test_classifiers_processed_in_order(self, mock_import):
        fake_module = MagicMock()
        mock_import.return_value = fake_module

        classifiers = [
            _make_classifier('seo_score',        cid=1),
            _make_classifier('readability_score', cid=2),
            _make_classifier('seo_rule_based',    cid=3),
        ]
        Classifier().load_classifier(classifiers, MagicMock(), MagicMock(), 'srv')

        ids_in_order = [c[0][0] for c in fake_module.main.call_args_list]
        self.assertEqual(ids_in_order, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
