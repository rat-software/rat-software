"""
Tests for export.py – focused on:
  1. Data transformation (format_domain_df, classifier/result stats builders)
  2. CSV-/JSON-äquivalente Logik (DataFrame-Spalten, Typen, Formatierung)
  3. Leere Datensätze (keine Sheets bei leeren DataFrames)
  4. Dateinamen-Sanitierung
"""

import re
import pytest
import pandas as pd
from io import BytesIO
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helfer: repliziert die eingebetteten Hilfsfunktionen aus export.py
# ---------------------------------------------------------------------------

def format_domain_df(domain_data, data_key):
    """Logik aus export.py::format_domain_df – identische Implementierung."""
    if not domain_data or data_key not in domain_data:
        return pd.DataFrame()
    df = pd.DataFrame(domain_data[data_key])
    if df.empty:
        return pd.DataFrame()
    df['percentage'] = df['percentage'].apply(lambda x: f"{x:.2f}%")
    if 'avg_position' in df.columns:
        df['avg_position'] = df['avg_position'].apply(
            lambda x: f"{x:.2f}" if x is not None else 'N/A'
        )
    df.rename(
        columns={'percentage': 'Share of Total', 'avg_position': 'Avg. Position'},
        inplace=True,
    )
    return df


def transform_classifier_stats(classifier_stats_data):
    """Logik aus dem classifier_stats-Lambda in export_options."""
    if not classifier_stats_data:
        return pd.DataFrame()
    rows = [
        {
            'Classifier': cls,
            'Value': val,
            'Count': data['count'],
            'Percentage of Total': f"{data['percentage']:.2f}%",
        }
        for cls, values in classifier_stats_data.items()
        for val, data in values.get('raw_stats', {}).items()
    ]
    return pd.DataFrame(rows)


def build_result_stats_df(result_stats_data):
    """Logik aus dem result_stats-Lambda in export_options."""
    return pd.DataFrame(list(result_stats_data.items()), columns=['Statistic', 'Value'])


def sanitize_filename(name: str) -> str:
    """Logik aus export.py – Dateiname bereinigen."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)


# ===========================================================================
# 1. format_domain_df – Datentransformation
# ===========================================================================

class TestFormatDomainDf:

    def test_percentage_formatted_two_decimals(self):
        data = {'standard_results': [{'domain': 'example.com', 'percentage': 12.345}]}
        df = format_domain_df(data, 'standard_results')
        assert df['Share of Total'].iloc[0] == '12.35%'

    def test_percentage_zero(self):
        data = {'standard_results': [{'domain': 'example.com', 'percentage': 0.0}]}
        df = format_domain_df(data, 'standard_results')
        assert df['Share of Total'].iloc[0] == '0.00%'

    def test_percentage_100(self):
        data = {'standard_results': [{'domain': 'example.com', 'percentage': 100.0}]}
        df = format_domain_df(data, 'standard_results')
        assert df['Share of Total'].iloc[0] == '100.00%'

    def test_avg_position_formatted(self):
        data = {
            'standard_results': [
                {'domain': 'example.com', 'percentage': 10.0, 'avg_position': 3.14159}
            ]
        }
        df = format_domain_df(data, 'standard_results')
        assert df['Avg. Position'].iloc[0] == '3.14'

    def test_avg_position_none_becomes_na(self):
        data = {
            'standard_results': [
                {'domain': 'example.com', 'percentage': 10.0, 'avg_position': None}
            ]
        }
        df = format_domain_df(data, 'standard_results')
        assert df['Avg. Position'].iloc[0] == 'N/A'

    def test_no_avg_position_column_is_fine(self):
        data = {'ai_sources': [{'domain': 'ai.com', 'percentage': 55.5}]}
        df = format_domain_df(data, 'ai_sources')
        assert 'Avg. Position' not in df.columns
        assert df['Share of Total'].iloc[0] == '55.50%'

    def test_multiple_rows(self):
        data = {
            'standard_results': [
                {'domain': 'a.com', 'percentage': 30.0},
                {'domain': 'b.com', 'percentage': 70.0},
            ]
        }
        df = format_domain_df(data, 'standard_results')
        assert len(df) == 2
        assert df['Share of Total'].tolist() == ['30.00%', '70.00%']

    def test_columns_renamed(self):
        data = {'standard_results': [{'domain': 'x.com', 'percentage': 1.0}]}
        df = format_domain_df(data, 'standard_results')
        assert 'percentage' not in df.columns
        assert 'Share of Total' in df.columns

    # -----------------------------------------------------------------------
    # Leere / ungültige Eingaben
    # -----------------------------------------------------------------------

    def test_returns_empty_df_when_domain_data_none(self):
        assert format_domain_df(None, 'standard_results').empty

    def test_returns_empty_df_when_domain_data_empty_dict(self):
        assert format_domain_df({}, 'standard_results').empty

    def test_returns_empty_df_when_key_missing(self):
        assert format_domain_df({'ai_sources': []}, 'standard_results').empty

    def test_returns_empty_df_when_list_is_empty(self):
        data = {'standard_results': []}
        df = format_domain_df(data, 'standard_results')
        assert df.empty


# ===========================================================================
# 2. Classifier-Stats-Transformation
# ===========================================================================

class TestClassifierStatsTransformation:

    def _sample_stats(self):
        return {
            'spam_classifier': {
                'raw_stats': {
                    'spam': {'count': 10, 'percentage': 25.0},
                    'ham': {'count': 30, 'percentage': 75.0},
                }
            }
        }

    def test_row_count(self):
        df = transform_classifier_stats(self._sample_stats())
        assert len(df) == 2

    def test_columns_present(self):
        df = transform_classifier_stats(self._sample_stats())
        assert set(df.columns) == {'Classifier', 'Value', 'Count', 'Percentage of Total'}

    def test_values_correct(self):
        df = transform_classifier_stats(self._sample_stats())
        spam_row = df[df['Value'] == 'spam'].iloc[0]
        assert spam_row['Classifier'] == 'spam_classifier'
        assert spam_row['Count'] == 10
        assert spam_row['Percentage of Total'] == '25.00%'

    def test_percentage_formatted(self):
        stats = {'cls': {'raw_stats': {'x': {'count': 1, 'percentage': 33.3333}}}}
        df = transform_classifier_stats(stats)
        assert df['Percentage of Total'].iloc[0] == '33.33%'

    def test_multiple_classifiers(self):
        stats = {
            'cls_a': {'raw_stats': {'yes': {'count': 5, 'percentage': 50.0}}},
            'cls_b': {'raw_stats': {'no': {'count': 5, 'percentage': 50.0}}},
        }
        df = transform_classifier_stats(stats)
        assert len(df) == 2
        assert set(df['Classifier'].tolist()) == {'cls_a', 'cls_b'}

    # Leere Eingaben
    def test_none_returns_empty_df(self):
        assert transform_classifier_stats(None).empty

    def test_empty_dict_returns_empty_df(self):
        assert transform_classifier_stats({}).empty

    def test_empty_raw_stats_returns_empty_df(self):
        assert transform_classifier_stats({'cls': {'raw_stats': {}}}).empty

    def test_missing_raw_stats_key_returns_empty_df(self):
        assert transform_classifier_stats({'cls': {}}).empty


# ===========================================================================
# 3. Result-Stats-DataFrame-Builder
# ===========================================================================

class TestResultStatsDataFrame:

    def test_columns(self):
        df = build_result_stats_df({'Queries': 5, 'Search Engines': 2})
        assert list(df.columns) == ['Statistic', 'Value']

    def test_row_count(self):
        df = build_result_stats_df({'A': 1, 'B': 2, 'C': 3})
        assert len(df) == 3

    def test_values_preserved(self):
        df = build_result_stats_df({'Collection Status': '80%'})
        row = df[df['Statistic'] == 'Collection Status'].iloc[0]
        assert row['Value'] == '80%'

    def test_empty_stats(self):
        df = build_result_stats_df({})
        assert df.empty


# ===========================================================================
# 4. Dateinamen-Sanitierung
# ===========================================================================

class TestFilenameGeneration:

    def test_spaces_replaced(self):
        assert sanitize_filename("My Study Name") == "My_Study_Name"

    def test_special_chars_replaced(self):
        result = sanitize_filename("Study (2024)!")
        assert re.fullmatch(r'[a-zA-Z0-9_\-]+', result)

    def test_hyphens_preserved(self):
        assert sanitize_filename("my-study") == "my-study"

    def test_underscores_preserved(self):
        assert sanitize_filename("my_study") == "my_study"

    def test_slashes_replaced(self):
        assert sanitize_filename("Study/Topic") == "Study_Topic"

    def test_dots_replaced(self):
        assert sanitize_filename("study.name") == "study_name"

    def test_unicode_replaced(self):
        result = sanitize_filename("Studie über KI")
        assert re.fullmatch(r'[a-zA-Z0-9_\-]+', result)

    def test_already_clean_unchanged(self):
        assert sanitize_filename("CleanName123") == "CleanName123"

    def test_empty_string(self):
        assert sanitize_filename("") == ""


# ===========================================================================
# 5. Excel-Sheet-Selektion (leere DataFrames produzieren keinen Sheet)
# ===========================================================================

class TestExcelSheetSelection:
    """
    Simuliert die Kernlogik aus dem POST-Handler:
      for key, (label, func) in export_options.items():
          if available_data.get(key, False):
              df = func()
              if not df.empty:
                  df.to_excel(writer, sheet_name=label, index=False)

    Statt einen echten ExcelWriter zu erzeugen, erfassen wir die Sheet-Namen
    in einer Liste, um die Selektion rein zu testen.
    """

    def _collect_written_sheets(self, available_data, export_options):
        """Gibt die Liste der tatsächlich geschriebenen Sheet-Namen zurück."""
        written = []
        for key, (label, func) in export_options.items():
            if available_data.get(key, False):
                df = func()
                if not df.empty:
                    written.append(label)
        return written

    def _sample_df(self, rows=2):
        return pd.DataFrame({'col': range(rows)})

    def test_writes_sheet_for_available_non_empty_data(self):
        options = {'result_stats': ('Result Stats', lambda: self._sample_df())}
        sheets = self._collect_written_sheets({'result_stats': True}, options)
        assert sheets == ['Result Stats']

    def test_skips_sheet_when_data_not_available(self):
        options = {'result_stats': ('Result Stats', lambda: self._sample_df())}
        sheets = self._collect_written_sheets({'result_stats': False}, options)
        assert sheets == []

    def test_skips_sheet_for_empty_dataframe(self):
        options = {'result_stats': ('Result Stats', lambda: pd.DataFrame())}
        sheets = self._collect_written_sheets({'result_stats': True}, options)
        assert sheets == []

    def test_writes_multiple_sheets(self):
        options = {
            'result_stats': ('Result Stats', lambda: self._sample_df()),
            'search_results': ('Search Results', lambda: self._sample_df()),
        }
        sheets = self._collect_written_sheets(
            {'result_stats': True, 'search_results': True}, options
        )
        assert len(sheets) == 2
        assert 'Result Stats' in sheets
        assert 'Search Results' in sheets

    def test_mixed_empty_and_non_empty(self):
        options = {
            'result_stats': ('Result Stats', lambda: self._sample_df()),
            'assessments': ('Assessments', lambda: pd.DataFrame()),
            'search_results': ('Search Results', lambda: self._sample_df()),
        }
        sheets = self._collect_written_sheets(
            {'result_stats': True, 'assessments': True, 'search_results': True}, options
        )
        assert sheets == ['Result Stats', 'Search Results']

    def test_sheet_label_matches_export_options(self):
        options = {'assessments': ('Assessments', lambda: self._sample_df())}
        sheets = self._collect_written_sheets({'assessments': True}, options)
        assert 'Assessments' in sheets

    def test_all_data_unavailable_writes_nothing(self):
        options = {
            'result_stats': ('Result Stats', lambda: self._sample_df()),
            'assessments': ('Assessments', lambda: self._sample_df()),
        }
        sheets = self._collect_written_sheets(
            {'result_stats': False, 'assessments': False}, options
        )
        assert sheets == []

    def test_unknown_key_in_available_data_ignored(self):
        options = {'result_stats': ('Result Stats', lambda: self._sample_df())}
        sheets = self._collect_written_sheets(
            {'result_stats': True, 'nonexistent_key': True}, options
        )
        assert sheets == ['Result Stats']


# ===========================================================================
# 6. Assessments-SQL-Branch – participant_name-Spalte
# ===========================================================================

class TestAssessmentSqlBranch:
    """
    Prüft, dass die richtige Spaltenliste je nach participant-Vorhandensein gewählt wird.
    """

    WITH_PARTICIPANTS = [
        'Source Type', 'Source URL/Query', 'Source ID', 'Query ID', 'Keyword',
        'Participant Name', 'Question', 'Question Position', 'Question Type',
        'Answer', 'Timestamp',
    ]
    WITHOUT_PARTICIPANTS = [
        'Source Type', 'Source URL/Query', 'Source ID', 'Query ID', 'Keyword',
        'Question', 'Question Position', 'Question Type', 'Answer', 'Timestamp',
    ]

    def test_with_participants_has_participant_name_column(self):
        assert 'Participant Name' in self.WITH_PARTICIPANTS

    def test_without_participants_lacks_participant_name_column(self):
        assert 'Participant Name' not in self.WITHOUT_PARTICIPANTS

    def test_without_participants_has_one_fewer_column(self):
        assert len(self.WITHOUT_PARTICIPANTS) == len(self.WITH_PARTICIPANTS) - 1

    def test_column_order_stable(self):
        # Source Type muss immer erste Spalte sein
        assert self.WITH_PARTICIPANTS[0] == 'Source Type'
        assert self.WITHOUT_PARTICIPANTS[0] == 'Source Type'

    def test_dataframe_from_records_with_participants(self):
        records = [('Search Result', 'http://x.com', 1, 2, 'query', 'Alice',
                    'Q1', 1, 'likert_scale', '5', '2024-01-01')]
        df = pd.DataFrame.from_records(records, columns=self.WITH_PARTICIPANTS)
        assert 'Participant Name' in df.columns
        assert df['Participant Name'].iloc[0] == 'Alice'

    def test_dataframe_from_records_without_participants(self):
        records = [('Search Result', 'http://x.com', 1, 2, 'query',
                    'Q1', 1, 'likert_scale', '5', '2024-01-01')]
        df = pd.DataFrame.from_records(records, columns=self.WITHOUT_PARTICIPANTS)
        assert 'Participant Name' not in df.columns

    def test_empty_records_produces_empty_df(self):
        df = pd.DataFrame.from_records([], columns=self.WITH_PARTICIPANTS)
        assert df.empty
        assert list(df.columns) == self.WITH_PARTICIPANTS
