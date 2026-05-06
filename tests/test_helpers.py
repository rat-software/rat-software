"""
Unit tests for rat-frontend/app/helpers.py

Covers percentage_calc: zero/negative total, type="int"/"float"/"str",
rounding behaviour, int/float/None inputs, unknown type.
"""
import sys
import os
import types
import importlib.util
import unittest

# ── Mock the entire Flask app package so helpers.py can be imported
# without a running Flask application or database connection.
_pkg = types.ModuleType('app')
_pkg.app = None
_pkg.db = None
_pkg.__path__ = []

sys.modules.setdefault('app', _pkg)

_forms = types.ModuleType('app.forms')
_forms.AnswerForm = type('AnswerForm', (), {})
sys.modules.setdefault('app.forms', _forms)

_models = types.ModuleType('app.models')
_models.Option = type('Option', (), {})
_models.Question = type('Question', (), {})
sys.modules.setdefault('app.models', _models)

_crontab = types.ModuleType('crontab')
_crontab.CronTab = type('CronTab', (), {})
sys.modules.setdefault('crontab', _crontab)

# markupsafe is a real Flask dependency — mock only if not installed
if 'markupsafe' not in sys.modules:
    _markupsafe = types.ModuleType('markupsafe')
    _markupsafe.Markup = lambda x: x
    sys.modules['markupsafe'] = _markupsafe

# Load helpers.py directly from its file path
_HELPERS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-frontend', 'app', 'helpers.py',
)
_spec = importlib.util.spec_from_file_location('app.helpers', _HELPERS_PATH)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = 'app'
sys.modules['app.helpers'] = _mod
_spec.loader.exec_module(_mod)

percentage_calc = _mod.percentage_calc


# ─────────────────────────────────────────────────────────────────
# percentage_calc
# ─────────────────────────────────────────────────────────────────

class TestPercentageCalcZeroTotal(unittest.TestCase):
    """Division durch Null / ungültiger Nenner"""

    def test_zero_total_returns_dash(self):
        self.assertEqual(percentage_calc(50, 0, 'int'), '-')

    def test_negative_total_returns_dash(self):
        self.assertEqual(percentage_calc(50, -10, 'int'), '-')

    def test_zero_total_all_types_return_dash(self):
        for t in ('int', 'float', 'str'):
            self.assertEqual(percentage_calc(100, 0, t), '-')


class TestPercentageCalcIntType(unittest.TestCase):
    """type='int' — ganzzahlige Prozentwerte"""

    def test_basic_quarter(self):
        self.assertEqual(percentage_calc(1, 4, 'int'), 25)

    def test_full_hundred_percent(self):
        self.assertEqual(percentage_calc(100, 100, 'int'), 100)

    def test_zero_value(self):
        self.assertEqual(percentage_calc(0, 100, 'int'), 0)

    def test_rounds_down(self):
        # 1/3 = 33.333… → 33
        self.assertEqual(percentage_calc(1, 3, 'int'), 33)

    def test_rounds_up(self):
        # 2/3 = 66.666… → 67
        self.assertEqual(percentage_calc(2, 3, 'int'), 67)

    def test_returns_int_type(self):
        self.assertIsInstance(percentage_calc(1, 4, 'int'), int)

    def test_integer_inputs(self):
        self.assertEqual(percentage_calc(25, 100, 'int'), 25)

    def test_float_inputs(self):
        self.assertEqual(percentage_calc(0.25, 1.0, 'int'), 25)

    def test_mixed_int_float_inputs(self):
        self.assertEqual(percentage_calc(1, 4.0, 'int'), 25)


class TestPercentageCalcFloatType(unittest.TestCase):
    """type='float' — gibt Ratio zurück, nicht *100"""

    def test_returns_ratio_not_percentage(self):
        # 1/4 = 0.25, NICHT 25
        self.assertAlmostEqual(percentage_calc(1, 4, 'float'), 0.25)

    def test_full_value_returns_one(self):
        self.assertAlmostEqual(percentage_calc(100, 100, 'float'), 1.0)

    def test_zero_value_returns_zero(self):
        self.assertAlmostEqual(percentage_calc(0, 100, 'float'), 0.0)

    def test_returns_float_type(self):
        self.assertIsInstance(percentage_calc(1, 4, 'float'), float)

    def test_float_inputs(self):
        self.assertAlmostEqual(percentage_calc(0.5, 2.0, 'float'), 0.25)


class TestPercentageCalcStrType(unittest.TestCase):
    """type='str' — formatierter String mit ' %'"""

    def test_basic_format(self):
        self.assertEqual(percentage_calc(1, 4, 'str'), '25 %')

    def test_full_hundred_percent(self):
        self.assertEqual(percentage_calc(100, 100, 'str'), '100 %')

    def test_zero_value(self):
        self.assertEqual(percentage_calc(0, 100, 'str'), '0 %')

    def test_rounded_value(self):
        # 1/3 = 33.333… → '33 %'
        self.assertEqual(percentage_calc(1, 3, 'str'), '33 %')

    def test_returns_string_type(self):
        self.assertIsInstance(percentage_calc(1, 4, 'str'), str)

    def test_contains_percent_sign(self):
        self.assertIn('%', percentage_calc(1, 4, 'str'))


class TestPercentageCalcNoneInputs(unittest.TestCase):
    """None als Eingabe — nicht abgefangen, TypeError erwartet"""

    def test_none_total_raises_type_error(self):
        with self.assertRaises(TypeError):
            percentage_calc(50, None, 'int')

    def test_none_value_raises_type_error(self):
        # None / total_value raises TypeError
        with self.assertRaises(TypeError):
            percentage_calc(None, 100, 'int')

    def test_none_both_raises_type_error(self):
        with self.assertRaises(TypeError):
            percentage_calc(None, None, 'int')


class TestPercentageCalcUnknownType(unittest.TestCase):
    """Unbekannter type-Wert — kein Branch trifft zu, result bleibt ungebunden"""

    def test_unknown_type_with_valid_total_raises(self):
        with self.assertRaises(ValueError):
            percentage_calc(50, 100, 'percent')

    def test_unknown_type_with_zero_total_returns_dash(self):
        # Bei total=0 wird result="-" gesetzt, bevor der type-Zweig erreicht wird
        self.assertEqual(percentage_calc(50, 0, 'percent'), '-')


if __name__ == '__main__':
    unittest.main()
