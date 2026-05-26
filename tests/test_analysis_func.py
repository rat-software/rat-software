"""
Unit tests for rat-frontend/app/views/analysis_func.py

Testbar ohne Datenbank:
  - convert_answer_stats_to_df  (reine Funktion)
  - Statistik-Mathematik        (mean, std dev, min/max — inline in get_answer_stats)
  - Overlap-Mathematik          (set intersection / union — inline in get_overlap_stats)
  - Engine-Name-Formatierung    (string-Logik in get_overlap_stats)
  - Early-Return-Zweige         (get_evaluation_stats, get_classifier_stats)
"""
import importlib.util
import os
import sys
import types
import unittest
from itertools import combinations
from unittest.mock import MagicMock

# ── Mock Flask/SQLAlchemy package so the module loads without a running app ──

_app_pkg = types.ModuleType('app')
_app_pkg.app = MagicMock()
_app_pkg.db  = MagicMock()
_app_pkg.__path__ = []
sys.modules.setdefault('app', _app_pkg)

_views_pkg = types.ModuleType('app.views')
_views_pkg.__path__ = []
sys.modules.setdefault('app.views', _views_pkg)

_models_mod = types.ModuleType('app.models')
for _n in ('Scraper', 'Answer', 'Result', 'ResultAi', 'ResultSource',
           'ClassifierResult', 'ResultAiSource', 'ResultType', 'ResultChatbot'):
    setattr(_models_mod, _n, MagicMock())
sys.modules.setdefault('app.models', _models_mod)

def _pct(value, total, t):
    if total <= 0:
        return '-'
    r = value / total
    if t == 'int':   return round(r * 100)
    if t == 'float': return r
    if t == 'str':   return f"{round(r * 100)} %"
    raise ValueError(t)

_helpers_mod = types.ModuleType('app.helpers')
_helpers_mod.percentage_calc = _pct
sys.modules.setdefault('app.helpers', _helpers_mod)

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-frontend', 'app', 'views', 'analysis_func.py',
)
_spec = importlib.util.spec_from_file_location('app.views.analysis_func', _PATH)
_mod  = importlib.util.module_from_spec(_spec)
_mod.__package__ = 'app.views'
sys.modules['app.views.analysis_func'] = _mod
_spec.loader.exec_module(_mod)

convert_answer_stats_to_df = _mod.convert_answer_stats_to_df
get_evaluation_stats        = _mod.get_evaluation_stats
get_classifier_stats        = _mod.get_classifier_stats


# ── Hilfsfunktionen für Test-Daten ───────────────────────────────────────────

def _question(title, q_type, by_type, qid=1, pos=1):
    return {'question_id': qid, 'title': title,
            'position': pos, 'type': q_type, 'by_type': by_type}

def _dist(*items):
    """Erstellt eine distribution-Liste aus (value, label, count, pct)-Tupeln."""
    return [{'value': v, 'label': l, 'count': c, 'percentage': p}
            for v, l, c, p in items]

def _num_stats(**kw):
    return {'numeric_stats': kw}

class _MockStudy:
    def __init__(self, **kw):
        self.id             = kw.get('id', 1)
        self.queries        = kw.get('queries', [])
        self.questions      = kw.get('questions', [])
        self.participants   = kw.get('participants', [])
        self.result_count   = kw.get('result_count', 10)
        self.live_link_mode = kw.get('live_link_mode', False)
        self.classifier     = kw.get('classifier', None)


# ─────────────────────────────────────────────────────────────────────────────
# convert_answer_stats_to_df — leere Eingaben
# ─────────────────────────────────────────────────────────────────────────────

class TestConvertToDfEmpty(unittest.TestCase):

    def test_none_returns_empty_dataframe(self):
        df = convert_answer_stats_to_df(None)
        self.assertTrue(df.empty)

    def test_empty_list_returns_empty_dataframe(self):
        df = convert_answer_stats_to_df([])
        self.assertTrue(df.empty)

    def test_question_with_empty_by_type_produces_no_rows(self):
        data = [_question('Q', 'likert_scale', {})]
        self.assertTrue(convert_answer_stats_to_df(data).empty)


# ─────────────────────────────────────────────────────────────────────────────
# convert_answer_stats_to_df — Kategorische Fragen (Distribution)
# ─────────────────────────────────────────────────────────────────────────────

class TestConvertToDfDistribution(unittest.TestCase):

    def _df(self, q_type):
        data = [_question('Q', q_type, {
            'Standard': {'distribution': _dist(
                ('5', 'Sehr gut', 10, 50.0),
                ('3', 'Neutral',   6, 30.0),
            )}
        })]
        return convert_answer_stats_to_df(data)

    def test_likert_scale_produces_rows(self):
        self.assertEqual(len(self._df('likert_scale')), 2)

    def test_true_false_produces_rows(self):
        self.assertEqual(len(self._df('true_false')), 2)

    def test_multiple_choice_produces_rows(self):
        self.assertEqual(len(self._df('multiple_choice')), 2)

    def test_distribution_count_column(self):
        df = self._df('likert_scale')
        self.assertListEqual(list(df['Count']), [10, 6])

    def test_distribution_label_column(self):
        df = self._df('likert_scale')
        self.assertIn('Sehr gut', df['Answer Label'].values)

    def test_distribution_value_column(self):
        df = self._df('likert_scale')
        self.assertIn('5', df['Answer Value'].values)

    def test_result_type_column_preserved(self):
        df = self._df('likert_scale')
        self.assertTrue((df['Result Type'] == 'Standard').all())

    def test_question_title_column_preserved(self):
        df = self._df('likert_scale')
        self.assertTrue((df['Question'] == 'Q').all())

    def test_text_question_not_included(self):
        data = [_question('T', 'text', {
            'Standard': {'comments': ['answer a', 'answer b']}
        })]
        self.assertTrue(convert_answer_stats_to_df(data).empty)


# ─────────────────────────────────────────────────────────────────────────────
# convert_answer_stats_to_df — Numerische Fragen (scale_number)
# ─────────────────────────────────────────────────────────────────────────────

class TestConvertToDfScaleNumber(unittest.TestCase):

    def _df(self, stats: dict):
        data = [_question('Score', 'scale_number', {
            'Standard': {'numeric_stats': stats}
        })]
        return convert_answer_stats_to_df(data)

    def test_scale_number_produces_rows(self):
        df = self._df({'count': 5, 'mean': 3.5, 'min': 1.0, 'max': 6.0})
        self.assertEqual(len(df), 4)  # count, mean, min, max

    def test_stat_labels_are_capitalised(self):
        df = self._df({'mean': 2.5})
        self.assertIn('Mean', df['Answer Label'].values)

    def test_float_values_formatted_to_2dp(self):
        df = self._df({'mean': 3.14159})
        row = df[df['Answer Label'] == 'Mean'].iloc[0]
        self.assertEqual(row['Answer Value'], '3.14')

    def test_integer_count_not_formatted_as_float(self):
        df = self._df({'count': 7})
        row = df[df['Answer Label'] == 'Count'].iloc[0]
        self.assertEqual(row['Answer Value'], 7)

    def test_count_and_share_columns_empty_for_scale(self):
        df = self._df({'mean': 1.0})
        self.assertEqual(df.iloc[0]['Count'], '')
        self.assertEqual(df.iloc[0]['Share (%)'], '')


# ─────────────────────────────────────────────────────────────────────────────
# convert_answer_stats_to_df — Formatierung & Spalten
# ─────────────────────────────────────────────────────────────────────────────

class TestConvertToDfFormatting(unittest.TestCase):

    def _simple_df(self):
        data = [_question('Q', 'likert_scale', {
            'Standard': {'distribution': _dist(('1', 'Yes', 3, 75.0))}
        })]
        return convert_answer_stats_to_df(data)

    def test_share_percentage_two_decimal_places(self):
        data = [_question('Q', 'likert_scale', {
            'Standard': {'distribution': _dist(('1', 'Yes', 1, 33.333))}
        })]
        df = convert_answer_stats_to_df(data)
        self.assertEqual(df.iloc[0]['Share (%)'], '33.33')

    def test_expected_columns_present(self):
        df = self._simple_df()
        for col in ('Question', 'Result Type', 'Type', 'Answer Label',
                    'Answer Value', 'Count', 'Share (%)'):
            self.assertIn(col, df.columns)

    def test_type_column_contains_question_type(self):
        df = self._simple_df()
        self.assertTrue((df['Type'] == 'likert_scale').all())

    def test_multiple_questions_stacked(self):
        data = [
            _question('Q1', 'likert_scale', {
                'Standard': {'distribution': _dist(('1', 'A', 2, 100.0))}
            }, qid=1),
            _question('Q2', 'true_false', {
                'Standard': {'distribution': _dist(('1', 'B', 3, 100.0))}
            }, qid=2),
        ]
        df = convert_answer_stats_to_df(data)
        self.assertEqual(len(df), 2)
        self.assertIn('Q1', df['Question'].values)
        self.assertIn('Q2', df['Question'].values)

    def test_multiple_result_types_per_question(self):
        data = [_question('Q', 'true_false', {
            'Standard': {'distribution': _dist(('1', 'Yes', 5, 100.0))},
            'AI':       {'distribution': _dist(('0', 'No',  2, 100.0))},
        })]
        df = convert_answer_stats_to_df(data)
        self.assertEqual(len(df), 2)
        self.assertIn('Standard', df['Result Type'].values)
        self.assertIn('AI', df['Result Type'].values)


# ─────────────────────────────────────────────────────────────────────────────
# Statistik-Mathematik (mean, population std dev, min/max)
# Repliziert exakt die Formeln aus get_answer_stats
# ─────────────────────────────────────────────────────────────────────────────

class TestStatisticalMath(unittest.TestCase):

    def _stats(self, nums):
        n = len(nums)
        m = sum(nums) / n
        var = sum((x - m) ** 2 for x in nums) / n
        return {'mean': m, 'std_dev': var ** 0.5, 'count': n,
                'min': min(nums), 'max': max(nums)}

    def test_mean_symmetric_values(self):
        self.assertAlmostEqual(self._stats([1, 2, 3, 4, 5])['mean'], 3.0)

    def test_mean_single_value(self):
        self.assertAlmostEqual(self._stats([7.0])['mean'], 7.0)

    def test_std_dev_known_result(self):
        # Dataset with population std dev = 2.0
        nums = [2, 4, 4, 4, 5, 5, 7, 9]
        self.assertAlmostEqual(self._stats(nums)['std_dev'], 2.0)

    def test_std_dev_single_value_is_zero(self):
        self.assertAlmostEqual(self._stats([42.0])['std_dev'], 0.0)

    def test_std_dev_identical_values_is_zero(self):
        self.assertAlmostEqual(self._stats([3.0, 3.0, 3.0])['std_dev'], 0.0)

    def test_min_max_correct(self):
        s = self._stats([10.0, 3.0, 7.0, 1.0, 9.0])
        self.assertEqual(s['min'], 1.0)
        self.assertEqual(s['max'], 10.0)

    def test_count_reflects_input_length(self):
        self.assertEqual(self._stats([1, 2, 3, 4])['count'], 4)

    def test_mean_float_inputs(self):
        self.assertAlmostEqual(self._stats([0.1, 0.2, 0.3])['mean'], 0.2)


# ─────────────────────────────────────────────────────────────────────────────
# Overlap-Mathematik (set intersection / union)
# Repliziert exakt die Formeln aus get_overlap_stats
# ─────────────────────────────────────────────────────────────────────────────

class TestOverlapMath(unittest.TestCase):

    def _calc(self, se_list):
        result = []
        for (n1, d1), (n2, d2) in combinations(se_list.items(), 2):
            result.append({
                'SE_Pair':         f'{n1}-{n2}',
                'SE_1':            n1,
                'SE_1 exclusive':  len(d1['Sources'] - d2['Sources']),
                'SE_2':            n2,
                'SE_2 exclusive':  len(d2['Sources'] - d1['Sources']),
                'Overlap':         len(d1['Sources'] & d2['Sources']),
                'Total':           len(d1['Sources'] | d2['Sources']),
            })
        return result

    def test_no_overlap(self):
        r = self._calc({
            'Google': {'Sources': {'a.com', 'b.com'}},
            'Bing':   {'Sources': {'c.com', 'd.com'}},
        })
        self.assertEqual(r[0]['Overlap'], 0)
        self.assertEqual(r[0]['Total'], 4)

    def test_full_overlap(self):
        r = self._calc({
            'Google': {'Sources': {'a.com', 'b.com'}},
            'Bing':   {'Sources': {'a.com', 'b.com'}},
        })
        self.assertEqual(r[0]['Overlap'], 2)
        self.assertEqual(r[0]['SE_1 exclusive'], 0)
        self.assertEqual(r[0]['SE_2 exclusive'], 0)

    def test_partial_overlap(self):
        r = self._calc({
            'Google': {'Sources': {'a.com', 'b.com', 'c.com'}},
            'Bing':   {'Sources': {'b.com', 'c.com', 'd.com'}},
        })
        self.assertEqual(r[0]['Overlap'], 2)
        self.assertEqual(r[0]['SE_1 exclusive'], 1)
        self.assertEqual(r[0]['SE_2 exclusive'], 1)
        self.assertEqual(r[0]['Total'], 4)

    def test_three_engines_produce_three_pairs(self):
        se = {k: {'Sources': {f'{k}.com'}} for k in ('A', 'B', 'C')}
        self.assertEqual(len(self._calc(se)), 3)

    def test_pair_name_format(self):
        r = self._calc({
            'Google': {'Sources': {'x.com'}},
            'Bing':   {'Sources': {'y.com'}},
        })
        self.assertEqual(r[0]['SE_Pair'], 'Google-Bing')

    def test_single_shared_url(self):
        r = self._calc({
            'A': {'Sources': {'shared.com', 'only_a.com'}},
            'B': {'Sources': {'shared.com', 'only_b.com'}},
        })
        self.assertEqual(r[0]['Overlap'], 1)
        self.assertEqual(r[0]['Total'], 3)


# ─────────────────────────────────────────────────────────────────────────────
# Engine-Name-Formatierung (string-Logik in get_overlap_stats)
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineNameFormatting(unittest.TestCase):

    def _fmt(self, engine_str):
        parts = engine_str.split('_')
        if len(parts) >= 3:
            return f"{parts[0].capitalize()} ({parts[1].upper()} / {parts[2].upper()})"
        return engine_str.replace('_', ' ').title()

    def test_three_part_engine_string(self):
        self.assertEqual(self._fmt('google_us_en'), 'Google (US / EN)')

    def test_two_part_falls_back_to_title(self):
        self.assertEqual(self._fmt('google_us'), 'Google Us')

    def test_single_word_title_cased(self):
        self.assertEqual(self._fmt('bing'), 'Bing')

    def test_four_parts_uses_first_three(self):
        result = self._fmt('google_de_de_extra')
        self.assertEqual(result, 'Google (DE / DE)')


# ─────────────────────────────────────────────────────────────────────────────
# Early-Return-Zweige (kein DB-Zugriff nötig)
# ─────────────────────────────────────────────────────────────────────────────

class TestEarlyReturns(unittest.TestCase):

    def test_evaluation_stats_zero_questions_returns_dict(self):
        study = _MockStudy(questions=[], participants=[])
        result = get_evaluation_stats(study)
        self.assertEqual(result['Questions'], 0)
        self.assertEqual(result['Evaluation Status'], '0%')
        self.assertEqual(result['Evaluations Skipped'], 0)

    def test_evaluation_stats_zero_questions_participant_count(self):
        study = _MockStudy(questions=[], participants=['p1', 'p2'])
        result = get_evaluation_stats(study)
        self.assertEqual(result['Participants'], 2)

    def test_classifier_stats_no_classifier_returns_none(self):
        study = _MockStudy(classifier=None)
        self.assertIsNone(get_classifier_stats(study))

    def test_classifier_stats_empty_classifier_returns_none(self):
        study = _MockStudy(classifier=[])
        self.assertIsNone(get_classifier_stats(study))

    def test_classifier_stats_live_link_mode_returns_none(self):
        study = _MockStudy(classifier=['some'], live_link_mode=True)
        self.assertIsNone(get_classifier_stats(study))


if __name__ == '__main__':
    unittest.main()
