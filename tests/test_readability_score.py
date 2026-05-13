"""
Unit tests for readability_score/libs/text_analyzer.py and readability_score.py

Covers: Text_Analyzer (word-count threshold, language routing, error handling),
        analyzeEn/analyzeDe methods, and the main() classifier orchestration.
"""
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Path setup ───────────────────────────────────────────────────────────────
_CLASSIFIER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'classifier', 'classifiers', 'readability_score',
)
_LIBS_DIR = os.path.join(_CLASSIFIER_DIR, 'libs')
sys.path.insert(0, _LIBS_DIR)
sys.path.insert(0, _CLASSIFIER_DIR)

# Stub lib_db and lib_helper so readability_score.py can be imported without
# the classifier framework being installed.
for _stub_name in ('lib_db', 'lib_helper'):
    if _stub_name not in sys.modules:
        _stub = types.ModuleType(_stub_name)
        _stub.DB = type('DB', (), {})
        _stub.Helper = type('Helper', (), {})
        sys.modules[_stub_name] = _stub

from text_analyzer import Text_Analyzer
from langdetect import LangDetectException

# ── Fixtures ─────────────────────────────────────────────────────────────────
_EN_TEXT = (
    "The quick brown fox jumps over the lazy dog near the riverbank every single morning "
    "while the sun rises slowly above the distant green mountains in the surrounding countryside "
    "and birds sing their cheerful songs to welcome the new day with warmth joy and happiness "
    "and children play happily in the fields with colorful kites flying high in the clear blue sky"
)

_DE_TEXT = (
    "Die schnelle braune Katze springt über den faulen Hund am Flussufer jeden Morgen "
    "wenn die Sonne langsam über die fernen grünen Berge im Hinterland aufgeht und die "
    "Vögel ihre fröhlichen Lieder singen um den neuen Tag mit Wärme und Freude zu begrüßen "
    "und Kinder spielen glücklich auf den Feldern mit bunten Drachen die hoch in den klaren "
    "blauen Himmel fliegen während die Bäume im Wind sanft schwingen und die Blumen blühen"
)


def _html(body_text: str) -> str:
    return f'<html><body><p>{body_text}</p></body></html>'


def _html_words(n: int, word: str = "the") -> str:
    return _html(' '.join([word] * n))


# ─────────────────────────────────────────────────────────────────────────────
# Text_Analyzer.analyze — word-count threshold
# ─────────────────────────────────────────────────────────────────────────────

class TestWordCountThreshold(unittest.TestCase):

    def setUp(self):
        self.tx = Text_Analyzer()

    def test_empty_body_returns_error(self):
        self.assertEqual(self.tx.analyze('<html><body></body></html>'), 'error')

    def test_99_words_returns_error(self):
        self.assertEqual(self.tx.analyze(_html_words(99)), 'error')

    def test_100_words_does_not_return_error(self):
        # 100 words passes the threshold; result may be float, unsupported-lang, or
        # undetectable — anything but the word-count sentinel
        result = self.tx.analyze(_html_words(100))
        self.assertNotEqual(result, 'error')

    def test_script_text_excluded_from_word_count(self):
        # 50 real words in <p>, 100 words inside <script> → total visible < 100
        html = (
            '<html><body>'
            '<p>' + ' '.join(['hello'] * 50) + '</p>'
            '<script>' + ' '.join(['var'] * 100) + '</script>'
            '</body></html>'
        )
        self.assertEqual(self.tx.analyze(html), 'error')

    def test_style_text_excluded_from_word_count(self):
        html = (
            '<html><body>'
            '<p>' + ' '.join(['hello'] * 50) + '</p>'
            '<style>' + ' '.join(['.class'] * 100) + '</style>'
            '</body></html>'
        )
        self.assertEqual(self.tx.analyze(html), 'error')


# ─────────────────────────────────────────────────────────────────────────────
# Text_Analyzer.analyze — language routing (mocked detect)
# ─────────────────────────────────────────────────────────────────────────────

class TestLanguageRouting(unittest.TestCase):

    def setUp(self):
        self.tx = Text_Analyzer()
        self.html_100 = _html_words(100)

    @patch('text_analyzer.detect', return_value='en')
    def test_english_detected_delegates_to_analyzeEn(self, _):
        with patch.object(self.tx, 'analyzeEn', return_value=65.5) as mock_en:
            result = self.tx.analyze(self.html_100)
        mock_en.assert_called_once()
        self.assertEqual(result, 65.5)

    @patch('text_analyzer.detect', return_value='de')
    def test_german_detected_delegates_to_analyzeDe(self, _):
        with patch.object(self.tx, 'analyzeDe', return_value=55.0) as mock_de:
            result = self.tx.analyze(self.html_100)
        mock_de.assert_called_once()
        self.assertEqual(result, 55.0)

    @patch('text_analyzer.detect', return_value='fr')
    def test_unsupported_language_returns_descriptive_string(self, _):
        result = self.tx.analyze(self.html_100)
        self.assertIn('fr', result)
        self.assertIn('not supported', result)

    @patch('text_analyzer.detect', side_effect=LangDetectException(0, ''))
    def test_lang_detect_exception_returns_message(self, _):
        self.assertEqual(self.tx.analyze(self.html_100), 'Language could not be detected')


# ─────────────────────────────────────────────────────────────────────────────
# Text_Analyzer.analyze — integration (real langdetect)
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeIntegration(unittest.TestCase):

    def setUp(self):
        self.tx = Text_Analyzer()

    def test_english_html_returns_float(self):
        result = self.tx.analyze(_html(_EN_TEXT * 3))
        self.assertIsInstance(result, float)

    def test_german_html_returns_float(self):
        result = self.tx.analyze(_html(_DE_TEXT * 3))
        self.assertIsInstance(result, float)

    def test_english_score_is_finite_float(self):
        import math
        score = self.tx.analyze(_html(_EN_TEXT * 3))
        self.assertIsInstance(score, float)
        self.assertTrue(math.isfinite(score))
        # Maximum Flesch Reading Ease is 121 (trivially easy text)
        self.assertLessEqual(score, 121)


# ─────────────────────────────────────────────────────────────────────────────
# Text_Analyzer.analyzeEn / analyzeDe
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeEnDe(unittest.TestCase):

    def setUp(self):
        self.tx = Text_Analyzer()

    def test_analyzeEn_returns_float(self):
        self.assertIsInstance(self.tx.analyzeEn(_EN_TEXT), float)

    def test_analyzeDe_returns_float(self):
        self.assertIsInstance(self.tx.analyzeDe(_DE_TEXT), float)

    def test_analyzeEn_score_at_most_121(self):
        # Flesch Reading Ease has a theoretical maximum of ~121 (trivially simple text)
        self.assertLessEqual(self.tx.analyzeEn(_EN_TEXT), 121)

    def test_analyzeDe_score_at_most_121(self):
        self.assertLessEqual(self.tx.analyzeDe(_DE_TEXT), 121)

    def test_analyzeEn_on_empty_string_returns_float(self):
        # textstat handles empty strings — just ensure no exception
        self.assertIsInstance(self.tx.analyzeEn(''), float)

    def test_analyzeDe_on_empty_string_returns_float(self):
        self.assertIsInstance(self.tx.analyzeDe(''), float)


# ─────────────────────────────────────────────────────────────────────────────
# main() — classify_results orchestration
# ─────────────────────────────────────────────────────────────────────────────

class TestMainClassifyResults(unittest.TestCase):
    """
    Tests for the inner classify_results function via main().
    db, helper, and job_server are replaced with MagicMocks.
    """

    def _run(self, results, code=None):
        import readability_score as rs
        db = MagicMock()
        helper = MagicMock()
        if code is not None:
            helper.decode_code.return_value = code
        db.get_results.return_value = results
        db.check_classification_result.return_value = None
        db.check_classification_result_not_in_process.return_value = False
        rs.main(classifier_id=1, db=db, helper=helper, job_server='test', study_id=42)
        return db, helper

    def _result(self, status_code=200, error_code=None):
        return {'id': 1, 'file_path': '/fake/path',
                'status_code': status_code, 'error_code': error_code}

    # ── No results ────────────────────────────────────────────────────────────

    def test_empty_results_does_nothing(self):
        db, _ = self._run([])
        db.insert_indicator.assert_not_called()
        db.update_classification_result.assert_not_called()

    # ── HTTP / error-code guards ──────────────────────────────────────────────

    def test_status_not_200_writes_error(self):
        db, _ = self._run([self._result(status_code=404)],
                          code='<html><body></body></html>')
        db.update_classification_result.assert_called_once_with('error', 1, 1)

    def test_error_code_set_writes_error(self):
        db, _ = self._run([self._result(error_code='timeout')],
                          code='<html><body></body></html>')
        db.update_classification_result.assert_called_once_with('error', 1, 1)

    def test_empty_code_writes_error(self):
        db, _ = self._run([self._result()], code='')
        db.update_classification_result.assert_called_once_with('error', 1, 1)

    # ── Not enough text ───────────────────────────────────────────────────────

    def test_too_few_words_no_indicator_inserted(self):
        db, _ = self._run([self._result()],
                          code='<html><body><p>too short</p></body></html>')
        db.insert_indicator.assert_not_called()
        db.update_classification_result.assert_called_once_with('error', 1, 1)

    # ── Successful English classification ─────────────────────────────────────

    def test_valid_english_html_inserts_reading_ease_indicator(self):
        html = _html(_EN_TEXT * 3)
        db, _ = self._run([self._result()], code=html)

        indicator_calls = [c for c in db.insert_indicator.call_args_list
                           if c[0][0] == 'Reading Ease']
        self.assertEqual(len(indicator_calls), 1,
                         "Expected exactly one 'Reading Ease' indicator")

        update_arg = db.update_classification_result.call_args[0][0]
        self.assertNotIn(update_arg, ('error', 'classifier_error'))

    def test_valid_english_html_score_is_formatted_float_string(self):
        html = _html(_EN_TEXT * 3)
        db, _ = self._run([self._result()], code=html)

        update_arg = db.update_classification_result.call_args[0][0]
        # Score must be a string representation of a float with two decimals, e.g. "65.43"
        try:
            float(update_arg)
        except (ValueError, TypeError):
            self.fail(f"Expected a numeric string, got: {update_arg!r}")

    # ── Exception handling ────────────────────────────────────────────────────

    def test_exception_in_analyze_writes_classifier_error(self):
        html = _html(_EN_TEXT * 3)
        with patch('text_analyzer.Text_Analyzer.analyze',
                   side_effect=RuntimeError("analysis failed")):
            db, _ = self._run([self._result()], code=html)
        db.update_classification_result.assert_called_once_with('classifier_error', 1, 1)

    # ── In-process marker ─────────────────────────────────────────────────────

    def test_in_process_marker_inserted_before_classification(self):
        import readability_score as rs
        db = MagicMock()
        helper = MagicMock()
        helper.decode_code.return_value = ''
        db.get_results.return_value = [self._result()]
        db.check_classification_result.return_value = None
        db.check_classification_result_not_in_process.return_value = False

        rs.main(classifier_id=1, db=db, helper=helper, job_server='test', study_id=42)

        db.insert_classification_result.assert_called_with(1, 'in process', 1, 'test')


if __name__ == '__main__':
    unittest.main()
