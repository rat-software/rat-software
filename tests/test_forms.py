"""
Unit tests for rat-frontend/app/forms.py

Testschwerpunkte:
  - Pflichtfelder     (InputRequired / FileRequired)
  - Dateiformat       (FileAllowed)
  - Bereichsgrenzen   (NumberRange min=1)
"""
import importlib.util
import io
import os
import sys
import types
import unittest

from flask import Flask
from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from werkzeug.test import EnvironBuilder

# ── flask_security stub (nicht installiert) ───────────────────────────────────
if 'flask_security' not in sys.modules:
    _fs = types.ModuleType('flask_security')
    _fs_forms = types.ModuleType('flask_security.forms')
    _fs_forms.RegisterForm = FlaskForm
    _fs_forms.SendConfirmationForm = FlaskForm
    _fs_forms.ForgotPasswordForm = FlaskForm
    sys.modules['flask_security'] = _fs
    sys.modules['flask_security.forms'] = _fs_forms

# ── forms.py laden ───────────────────────────────────────────────────────────
_FORMS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-frontend', 'app', 'forms.py',
)
_spec = importlib.util.spec_from_file_location('app_forms', _FORMS_PATH)
_mod  = importlib.util.module_from_spec(_spec)
sys.modules['app_forms'] = _mod
_spec.loader.exec_module(_mod)

StudyForm               = _mod.StudyForm
UploadResultsForm       = _mod.UploadResultsForm
ImportQuestionsForm     = _mod.ImportQuestionsForm
RangeForm               = _mod.RangeForm
StudySettingsForm       = _mod.StudySettingsForm
KeywordsForm            = _mod.KeywordsForm
QuerySamplerWizardForm  = _mod.QuerySamplerWizardForm
EditQsStudyForm         = _mod.EditQsStudyForm

# ── minimale Flask-App (CSRF deaktiviert) ─────────────────────────────────────
_app = Flask(__name__)
_app.config.update({
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'SECRET_KEY': 'test-secret',
    'RECAPTCHA_PUBLIC_KEY': 'test',
    'RECAPTCHA_PRIVATE_KEY': 'test',
})


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _ctx(data: dict | None = None):
    """Request-Context mit optionalen POST-Textfeldern."""
    if data is None:
        return _app.test_request_context('/')
    env = EnvironBuilder(method='POST', data=data).get_environ()
    return _app.request_context(env)

def _file_ctx(field: str, filename: str, content: bytes = b'data'):
    """Request-Context mit simuliertem Datei-Upload."""
    env = EnvironBuilder(
        method='POST',
        data={field: (io.BytesIO(content), filename)},
    ).get_environ()
    return _app.request_context(env)

def _text_form(FormClass, fields: dict):
    """Instantiiert ein Formular mit Text-Felddaten (kein Datei-Upload)."""
    return FormClass(formdata=MultiDict(list(fields.items())))

def _errors(form, field: str):
    return getattr(form, field).errors


# ─────────────────────────────────────────────────────────────────────────────
# StudyForm — Pflichtfeld name
# ─────────────────────────────────────────────────────────────────────────────

class TestStudyFormRequired(unittest.TestCase):

    def test_valid_name_passes(self):
        with _app.test_request_context('/'):
            self.assertTrue(_text_form(StudyForm, {'name': 'Meine Studie'}).validate())

    def test_empty_name_fails(self):
        with _app.test_request_context('/'):
            form = _text_form(StudyForm, {'name': ''})
            self.assertFalse(form.validate())
            self.assertTrue(_errors(form, 'name'))

    def test_whitespace_only_name_passes_input_required(self):
        # InputRequired (unlike DataRequired) does NOT strip whitespace
        with _app.test_request_context('/'):
            form = _text_form(StudyForm, {'name': '   '})
            self.assertTrue(form.validate())

    def test_description_is_optional(self):
        with _app.test_request_context('/'):
            form = _text_form(StudyForm, {'name': 'Studie'})
            self.assertTrue(form.validate())


# ─────────────────────────────────────────────────────────────────────────────
# UploadResultsForm — Pflichtfeld & erlaubte Dateiformate
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadResultsFileAllowed(unittest.TestCase):

    def _validate(self, filename):
        with _file_ctx('results_file', filename):
            form = UploadResultsForm()
            form.validate()
            return form

    def test_zip_file_is_allowed(self):
        self.assertTrue(self._validate('data.zip').validate())

    def test_json_file_is_allowed(self):
        self.assertTrue(self._validate('data.json').validate())

    def test_csv_file_is_allowed(self):
        self.assertTrue(self._validate('data.csv').validate())

    def test_txt_file_is_rejected(self):
        form = self._validate('data.txt')
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'results_file'))

    def test_pdf_file_is_rejected(self):
        self.assertFalse(self._validate('data.pdf').validate())

    def test_exe_file_is_rejected(self):
        self.assertFalse(self._validate('malware.exe').validate())

    def test_uppercase_extension_is_allowed(self):
        self.assertTrue(self._validate('DATA.ZIP').validate())


class TestUploadResultsRequired(unittest.TestCase):

    def test_no_file_fails(self):
        with _ctx({'submit_upload': 'Upload Data'}):
            form = UploadResultsForm()
            self.assertFalse(form.validate())
            self.assertTrue(_errors(form, 'results_file'))


# ─────────────────────────────────────────────────────────────────────────────
# ImportQuestionsForm — nur JSON erlaubt
# ─────────────────────────────────────────────────────────────────────────────

class TestImportQuestionsFileAllowed(unittest.TestCase):

    def _validate(self, filename):
        with _file_ctx('file', filename):
            form = ImportQuestionsForm()
            form.validate()
            return form

    def test_json_file_is_allowed(self):
        self.assertTrue(self._validate('questions.json').validate())

    def test_csv_file_is_rejected(self):
        self.assertFalse(self._validate('questions.csv').validate())

    def test_zip_file_is_rejected(self):
        self.assertFalse(self._validate('questions.zip').validate())

    def test_txt_file_is_rejected(self):
        self.assertFalse(self._validate('questions.txt').validate())

    def test_no_file_fails(self):
        with _ctx({}):
            form = ImportQuestionsForm()
            self.assertFalse(form.validate())
            self.assertTrue(_errors(form, 'file'))


# ─────────────────────────────────────────────────────────────────────────────
# RangeForm — Bereichsgrenzen (min=1)
# ─────────────────────────────────────────────────────────────────────────────

class TestRangeFormBounds(unittest.TestCase):

    def _form(self, start, end):
        with _app.test_request_context('/'):
            return _text_form(RangeForm, {'start_range': str(start), 'end_range': str(end)})

    def test_both_at_minimum_passes(self):
        self.assertTrue(self._form(1, 1).validate())

    def test_large_values_pass(self):
        self.assertTrue(self._form(100, 200).validate())

    def test_start_zero_fails(self):
        form = self._form(0, 10)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'start_range'))

    def test_start_negative_fails(self):
        form = self._form(-5, 10)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'start_range'))

    def test_end_zero_fails(self):
        form = self._form(1, 0)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'end_range'))

    def test_end_negative_fails(self):
        form = self._form(5, -1)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'end_range'))

    def test_both_zero_fails_both_fields(self):
        form = self._form(0, 0)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'start_range'))
        self.assertTrue(_errors(form, 'end_range'))


# ─────────────────────────────────────────────────────────────────────────────
# StudySettingsForm — Bereichsgrenzen & optionale Felder
# ─────────────────────────────────────────────────────────────────────────────

class TestStudySettingsFormBounds(unittest.TestCase):

    def _form(self, result_count=10, max_results=None):
        fields = {'result_count': str(result_count)}
        if max_results is not None:
            fields['max_results_per_participant'] = str(max_results)
        with _app.test_request_context('/'):
            return _text_form(StudySettingsForm, fields)

    def test_result_count_one_passes(self):
        self.assertTrue(self._form(result_count=1).validate())

    def test_result_count_zero_fails(self):
        form = self._form(result_count=0)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'result_count'))

    def test_result_count_negative_fails(self):
        form = self._form(result_count=-1)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'result_count'))

    def test_max_results_optional_absent_passes(self):
        self.assertTrue(self._form(result_count=10, max_results=None).validate())

    def test_max_results_one_passes(self):
        self.assertTrue(self._form(result_count=10, max_results=1).validate())

    def test_max_results_zero_fails(self):
        form = self._form(result_count=10, max_results=0)
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'max_results_per_participant'))


# ─────────────────────────────────────────────────────────────────────────────
# KeywordsForm — Pflichtfeld keywords
# ─────────────────────────────────────────────────────────────────────────────

class TestKeywordsFormRequired(unittest.TestCase):

    def _form(self, keywords):
        with _app.test_request_context('/'):
            form = _text_form(KeywordsForm, {'keywords': keywords,
                                             'language_criterion': '1',
                                             'region_criterion': '1'})
            # SelectFields need choices set dynamically (no defaults in form)
            form.language_criterion.choices = [(1, 'English'), (2, 'German')]
            form.region_criterion.choices   = [(1, 'Global'), (2, 'Germany')]
            return form

    def test_with_keywords_passes(self):
        self.assertTrue(self._form('seo python').validate())

    def test_empty_keywords_fails(self):
        form = self._form('')
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'keywords'))

    def test_whitespace_only_passes_input_required(self):
        # InputRequired does NOT strip whitespace — that is DataRequired's job
        self.assertTrue(self._form('   ').validate())


# ─────────────────────────────────────────────────────────────────────────────
# QuerySamplerWizardForm — mehrere Pflichtfelder
# ─────────────────────────────────────────────────────────────────────────────

class TestQuerySamplerWizardRequired(unittest.TestCase):

    def _make(self, overrides=None):
        fields = {
            'name': 'Test Study',
            'seed_keywords': 'python seo',
            'geotargets': '1',
            'languages': '1',
        }
        if overrides:
            fields.update(overrides)
        with _app.test_request_context('/'):
            form = _text_form(QuerySamplerWizardForm, fields)
            form.geotargets.choices  = [(1, 'USA'), (2, 'DE')]
            form.languages.choices   = [(1, 'English'), (2, 'German')]
            return form

    def test_all_required_fields_passes(self):
        self.assertTrue(self._make().validate())

    def test_missing_name_fails(self):
        form = self._make({'name': ''})
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'name'))

    def test_missing_seed_keywords_fails(self):
        form = self._make({'seed_keywords': ''})
        self.assertFalse(form.validate())
        self.assertTrue(_errors(form, 'seed_keywords'))

    def test_description_is_optional(self):
        self.assertTrue(self._make({'description': ''}).validate())


# ─────────────────────────────────────────────────────────────────────────────
# EditQsStudyForm — Pflichtfeld name
# ─────────────────────────────────────────────────────────────────────────────

class TestEditQsStudyRequired(unittest.TestCase):

    def test_valid_name_passes(self):
        with _app.test_request_context('/'):
            form = _text_form(EditQsStudyForm, {'name': 'Update Study'})
            self.assertTrue(form.validate())

    def test_empty_name_fails(self):
        with _app.test_request_context('/'):
            form = _text_form(EditQsStudyForm, {'name': ''})
            self.assertFalse(form.validate())
            self.assertTrue(_errors(form, 'name'))

    def test_new_keywords_optional(self):
        with _app.test_request_context('/'):
            form = _text_form(EditQsStudyForm, {'name': 'Study', 'new_keywords': ''})
            self.assertTrue(form.validate())


if __name__ == '__main__':
    unittest.main()
