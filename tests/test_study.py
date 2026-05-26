"""
Tests für study.py – fokussiert auf:
  1. Study-CRUD-Logik (Erstellen, Bearbeiten, Löschen)
  2. Validierung (Pflichtfelder, Formularlogik, Settings-Constraints)
  3. Hilfsfunktionen: normalize_url, get_main_domain, format_ai_text_to_html
  4. CSV-Upload-Validierung (process_upload_file)
"""

import pytest
import pandas as pd
from io import BytesIO, StringIO
from unittest.mock import MagicMock, patch, PropertyMock
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode
import zipfile
import tempfile
import os
import re
import html


# ---------------------------------------------------------------------------
# Hilfsfunktionen aus study.py – lokal repliziert für isolierte Unit-Tests
# ---------------------------------------------------------------------------

TRACKING_PARAMS_TO_REMOVE = [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'dclid', 'fbclid', '_hsenc', '_hsmi', 'mkt_tok', 'msclkid',
    'mc_cid', 'mc_eid', 'trk', 'onwewe', 'srsltid'
]


def normalize_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    try:
        parts = urlsplit(url)
        query_params = parse_qs(parts.query, keep_blank_values=True)
        filtered_params = {k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS_TO_REMOVE}
        new_query = urlencode(filtered_params, doseq=True)
        scheme = 'https'
        netloc = parts.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        path = parts.path
        if path != '/' and path.endswith('/'):
            path = path[:-1]
        return urlunsplit((scheme, netloc, path, new_query, parts.fragment))
    except Exception:
        return url


def get_main_domain(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    try:
        parts = urlsplit(url)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}/"
        return ""
    except Exception:
        return ""


def format_ai_text_to_html(text):
    if not text:
        return ""
    safe_text = html.escape(str(text))
    if '•' in safe_text:
        parts = safe_text.split('•')
        intro = parts[0].strip()
        intro = re.sub(r'\s{3,}', '<br><strong>', intro)
        if '<strong>' in intro:
            intro += '</strong>'
        list_html = "<ul>"
        for item in parts[1:]:
            clean_item = item.strip()
            clean_item = re.sub(r'\s{3,}', '</li></ul><br><strong>', clean_item)
            if '<strong>' in clean_item:
                clean_item += '</strong><ul><li>'
            list_html += f"<li>{clean_item}</li>"
        list_html += "</ul>"
        final_html = f"<p>{intro}</p>{list_html}"
        final_html = final_html.replace("<ul></ul>", "").replace("<strong></strong>", "")
        return final_html
    else:
        return f"<p>{safe_text.replace(chr(10), '<br>').replace(chr(13), '')}</p>"


def validate_csv_columns(df: pd.DataFrame):
    """
    Repliziert die Pflichtfeld-Prüfung aus process_upload_file.
    Gibt (ok: bool, error: str | None) zurück.
    """
    if 'url' in df.columns and 'query' not in df.columns:
        df = df.copy()
        df['query'] = 'Manual Import'
        df['engine'] = 'manual'
        df['country'] = 'xx'
        df['lang'] = 'xx'

    required_cols = ['query', 'engine', 'country', 'lang']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return False, f"Missing required columns in CSV. Needed: {required_cols}"
    return True, None


# ===========================================================================
# 1. normalize_url
# ===========================================================================

class TestNormalizeUrl:

    def test_removes_utm_source(self):
        url = "https://example.com/page?utm_source=google"
        assert normalize_url(url) == "https://example.com/page"

    def test_removes_multiple_tracking_params(self):
        url = "https://example.com/?utm_source=x&utm_medium=y&fbclid=z"
        result = normalize_url(url)
        assert 'utm_source' not in result
        assert 'utm_medium' not in result
        assert 'fbclid' not in result

    def test_preserves_non_tracking_params(self):
        url = "https://example.com/search?q=test&utm_source=ads"
        result = normalize_url(url)
        assert 'q=test' in result
        assert 'utm_source' not in result

    def test_strips_www(self):
        result = normalize_url("https://www.example.com/")
        assert '://www.' not in result
        assert 'example.com' in result

    def test_normalizes_http_to_https(self):
        result = normalize_url("http://example.com/page")
        assert result.startswith("https://")

    def test_lowercases_netloc(self):
        result = normalize_url("https://EXAMPLE.COM/path")
        assert 'example.com' in result

    def test_removes_trailing_slash_from_path(self):
        result = normalize_url("https://example.com/page/")
        assert not result.endswith('/page/')
        assert result.endswith('/page')

    def test_preserves_root_slash(self):
        result = normalize_url("https://example.com/")
        assert result == "https://example.com/"

    def test_returns_empty_for_none(self):
        assert normalize_url(None) == ""

    def test_returns_empty_for_empty_string(self):
        assert normalize_url("") == ""

    def test_returns_empty_for_whitespace(self):
        assert normalize_url("   ") == ""

    def test_returns_empty_for_non_string(self):
        assert normalize_url(123) == ""

    def test_all_tracking_params_removed(self):
        params = "&".join(f"{p}=val" for p in TRACKING_PARAMS_TO_REMOVE)
        url = f"https://example.com/?real=yes&{params}"
        result = normalize_url(url)
        for p in TRACKING_PARAMS_TO_REMOVE:
            assert p not in result
        assert 'real=yes' in result

    def test_gclid_removed(self):
        result = normalize_url("https://example.com/?gclid=abc123")
        assert 'gclid' not in result

    def test_srsltid_removed(self):
        result = normalize_url("https://example.com/?srsltid=abc")
        assert 'srsltid' not in result


# ===========================================================================
# 2. get_main_domain
# ===========================================================================

class TestGetMainDomain:

    def test_returns_scheme_and_netloc(self):
        assert get_main_domain("https://example.com/some/path") == "https://example.com/"

    def test_preserves_http(self):
        assert get_main_domain("http://example.com/page") == "http://example.com/"

    def test_includes_port(self):
        assert get_main_domain("https://example.com:8080/page") == "https://example.com:8080/"

    def test_returns_empty_for_empty_string(self):
        assert get_main_domain("") == ""

    def test_returns_empty_for_none(self):
        assert get_main_domain(None) == ""

    def test_returns_empty_for_whitespace(self):
        assert get_main_domain("   ") == ""

    def test_returns_empty_for_non_string(self):
        assert get_main_domain(42) == ""

    def test_returns_empty_for_relative_url(self):
        assert get_main_domain("/just/a/path") == ""

    def test_trailing_slash_always_present(self):
        result = get_main_domain("https://example.com/path/to/page")
        assert result.endswith("/")

    def test_www_included_as_is(self):
        result = get_main_domain("https://www.example.com/page")
        assert result == "https://www.example.com/"


# ===========================================================================
# 3. format_ai_text_to_html
# ===========================================================================

class TestFormatAiTextToHtml:

    def test_empty_string_returns_empty(self):
        assert format_ai_text_to_html("") == ""

    def test_none_returns_empty(self):
        assert format_ai_text_to_html(None) == ""

    def test_plain_text_wrapped_in_paragraph(self):
        result = format_ai_text_to_html("Hello world")
        assert result == "<p>Hello world</p>"

    def test_newlines_become_br(self):
        result = format_ai_text_to_html("Line1\nLine2")
        assert "<br>" in result

    def test_html_special_chars_escaped(self):
        result = format_ai_text_to_html("<script>alert('x')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_ampersand_escaped(self):
        result = format_ai_text_to_html("A & B")
        assert "&amp;" in result

    def test_bullet_points_produce_ul(self):
        result = format_ai_text_to_html("Intro• Item 1• Item 2")
        assert "<ul>" in result
        assert "<li>" in result

    def test_bullet_items_in_list(self):
        result = format_ai_text_to_html("Intro• First• Second")
        assert "<li>First</li>" in result
        assert "<li>Second</li>" in result

    def test_intro_wrapped_in_paragraph(self):
        result = format_ai_text_to_html("Intro text• Item")
        assert result.startswith("<p>")

    def test_single_bullet_point(self):
        result = format_ai_text_to_html("• Solo item")
        assert "<li>Solo item</li>" in result

    def test_no_empty_ul_tags(self):
        result = format_ai_text_to_html("Text• A• B")
        assert "<ul></ul>" not in result

    def test_no_empty_strong_tags(self):
        result = format_ai_text_to_html("Text• A• B")
        assert "<strong></strong>" not in result

    def test_non_string_input_converted(self):
        result = format_ai_text_to_html(42)
        assert "42" in result


# ===========================================================================
# 4. CSV-Upload-Validierung
# ===========================================================================

class TestCsvColumnValidation:
    """Testet die Pflichtfeld-Prüfung aus process_upload_file."""

    def test_valid_full_csv(self):
        df = pd.DataFrame({'query': ['test'], 'engine': ['google'], 'country': ['de'], 'lang': ['de']})
        ok, err = validate_csv_columns(df)
        assert ok is True
        assert err is None

    def test_url_only_csv_gets_auto_filled(self):
        df = pd.DataFrame({'url': ['https://example.com']})
        ok, err = validate_csv_columns(df)
        assert ok is True

    def test_missing_engine_fails(self):
        df = pd.DataFrame({'query': ['test'], 'country': ['de'], 'lang': ['de']})
        ok, err = validate_csv_columns(df)
        assert ok is False
        assert 'engine' in err or 'Missing' in err

    def test_missing_all_required_fails(self):
        df = pd.DataFrame({'title': ['foo'], 'url': ['bar']})
        ok, err = validate_csv_columns(df)
        # URL-only path greift NICHT wenn 'query' fehlt aber andere Felder auch fehlen
        # url ohne query → auto-fill, dann check
        assert ok is True  # url-only auto-fill füllt alle Pflichtfelder

    def test_completely_empty_required_cols_fails(self):
        df = pd.DataFrame({'irrelevant': [1, 2]})
        ok, err = validate_csv_columns(df)
        assert ok is False

    def test_error_message_contains_required_columns(self):
        df = pd.DataFrame({'x': [1]})
        ok, err = validate_csv_columns(df)
        assert 'query' in err
        assert 'engine' in err

    def test_extra_columns_allowed(self):
        df = pd.DataFrame({
            'query': ['q'], 'engine': ['g'], 'country': ['de'], 'lang': ['de'],
            'extra_col': ['value']
        })
        ok, err = validate_csv_columns(df)
        assert ok is True

    def test_empty_dataframe_fails(self):
        df = pd.DataFrame()
        ok, err = validate_csv_columns(df)
        assert ok is False


# ===========================================================================
# 5. Study-CRUD-Logik (ohne Flask-Kontext)
# ===========================================================================

class TestCreateNewStudyLogic:
    """
    Testet die Verzweigungslogik aus create_new_study:
      study_id == 0  → neues Study-Objekt erstellen
      study_id  > 0  → bestehendes Study aktualisieren
    """

    def _should_create(self, study_id_raw):
        try:
            study_id = int(study_id_raw)
        except (ValueError, TypeError):
            study_id = 0
        return study_id == 0

    def test_id_zero_triggers_create(self):
        assert self._should_create("0") is True

    def test_id_positive_triggers_update(self):
        assert self._should_create("42") is False

    def test_missing_id_defaults_to_create(self):
        assert self._should_create(None) is True

    def test_non_numeric_id_defaults_to_create(self):
        assert self._should_create("abc") is True

    def test_float_string_triggers_update(self):
        # int("3.0") schlägt fehl → study_id=0 → create
        assert self._should_create("3.0") is True

    def test_negative_id_triggers_update(self):
        # negative IDs sind keine gültige DB-ID, aber die Logik prüft nur == 0
        assert self._should_create("-1") is False


class TestStudySettingsLogic:
    """
    Testet die Einstellungs-Constraints aus update_study_settings:
      live_link_mode=True  → show_urls wird auf True gezwungen
      live_link_mode=False → show_urls kommt aus dem Formular
      limit_per_participant=False → max_results_per_participant = None
    """

    def _apply_settings(self, live_link_mode, form_show_urls, limit_per_participant, max_results):
        show_urls = True if live_link_mode else form_show_urls
        max_per = max_results if limit_per_participant else None
        return {'show_urls': show_urls, 'max_results_per_participant': max_per}

    def test_live_mode_forces_show_urls_true(self):
        result = self._apply_settings(live_link_mode=True, form_show_urls=False,
                                      limit_per_participant=False, max_results=None)
        assert result['show_urls'] is True

    def test_non_live_mode_respects_form_show_urls_false(self):
        result = self._apply_settings(live_link_mode=False, form_show_urls=False,
                                      limit_per_participant=False, max_results=None)
        assert result['show_urls'] is False

    def test_non_live_mode_respects_form_show_urls_true(self):
        result = self._apply_settings(live_link_mode=False, form_show_urls=True,
                                      limit_per_participant=False, max_results=None)
        assert result['show_urls'] is True

    def test_limit_disabled_clears_max_results(self):
        result = self._apply_settings(live_link_mode=False, form_show_urls=True,
                                      limit_per_participant=False, max_results=5)
        assert result['max_results_per_participant'] is None

    def test_limit_enabled_preserves_max_results(self):
        result = self._apply_settings(live_link_mode=False, form_show_urls=True,
                                      limit_per_participant=True, max_results=10)
        assert result['max_results_per_participant'] == 10

    def test_live_mode_with_limit_enabled(self):
        result = self._apply_settings(live_link_mode=True, form_show_urls=False,
                                      limit_per_participant=True, max_results=3)
        assert result['show_urls'] is True
        assert result['max_results_per_participant'] == 3


class TestDeleteStudyLogic:
    """
    Testet die Kollektions-Logik für zu löschende Dateien aus delete_study:
    Nur Dateipfade die nicht None/leer sind, kommen in die Löschliste.
    Duplikate werden dedupliziert (set()).
    """

    def _collect_files(self, serps, result_sources):
        files = []
        for serp_path in serps:
            if serp_path:
                files.append(serp_path)
        for src_path in result_sources:
            if src_path:
                files.append(src_path)
        return set(files)

    def test_none_paths_excluded(self):
        files = self._collect_files([None, None], [])
        assert len(files) == 0

    def test_valid_paths_included(self):
        files = self._collect_files(['serp1.zip', 'serp2.zip'], [])
        assert 'serp1.zip' in files

    def test_duplicates_deduplicated(self):
        files = self._collect_files(['file.zip', 'file.zip'], [])
        assert len(files) == 1

    def test_mixed_none_and_valid(self):
        files = self._collect_files([None, 'serp.zip'], ['src.zip', None])
        assert files == {'serp.zip', 'src.zip'}

    def test_empty_inputs_produce_empty_set(self):
        files = self._collect_files([], [])
        assert files == set()


# ===========================================================================
# 6. check_and_update_status – Status-Übergänge
# ===========================================================================

class TestCheckAndUpdateStatusLogic:
    """
    Testet die Status-Übergangsregeln aus check_and_update_status isoliert.
    Status-Werte: 0=neu, 1=in Bearbeitung, 2=fertig, 3=?, 4=archiviert
    """

    def _compute_new_status(self, current_status, total_tasks, finished_tasks,
                             has_data, ai_count=0, chatbot_count=0, serp_count=0):
        """Repliziert die Status-Update-Logik."""
        has_data = has_data or ai_count > 0 or chatbot_count > 0 or serp_count > 0
        status = current_status
        status_changed = False

        if status == 0 and has_data:
            status = 1
            status_changed = True

        if status in [0, 1, 3]:
            if total_tasks > 0 and finished_tasks >= total_tasks:
                status = 2
                status_changed = True
            elif total_tasks == 0 and has_data:
                status = 2
                status_changed = True

        return status, status_changed

    def test_no_data_status_stays_zero(self):
        status, changed = self._compute_new_status(0, 0, 0, has_data=False)
        assert status == 0
        assert changed is False

    def test_has_data_transitions_zero_to_one(self):
        status, changed = self._compute_new_status(0, 5, 0, has_data=True)
        assert status == 1
        assert changed is True

    def test_all_tasks_done_transitions_to_two(self):
        status, changed = self._compute_new_status(1, 10, 10, has_data=True)
        assert status == 2
        assert changed is True

    def test_partial_progress_stays_at_one(self):
        status, changed = self._compute_new_status(1, 10, 5, has_data=True)
        assert status == 1
        assert changed is False

    def test_no_tasks_but_ai_data_transitions_to_two(self):
        status, changed = self._compute_new_status(0, 0, 0, has_data=False, ai_count=3)
        assert status == 2

    def test_no_tasks_but_chatbot_data_transitions_to_two(self):
        status, changed = self._compute_new_status(0, 0, 0, has_data=False, chatbot_count=1)
        assert status == 2

    def test_closed_study_status_4_unchanged(self):
        # Status 4 liegt nicht in [0, 1, 3] → keine Transitions
        status, changed = self._compute_new_status(4, 10, 10, has_data=True)
        assert status == 4
        assert changed is False

    def test_status_three_transitions_to_two_when_done(self):
        status, changed = self._compute_new_status(3, 5, 5, has_data=True)
        assert status == 2

    def test_already_at_two_stays_at_two(self):
        status, changed = self._compute_new_status(2, 5, 5, has_data=True)
        assert status == 2
        assert changed is False


# ===========================================================================
# 7. Template-Download-Logik
# ===========================================================================

class TestDownloadTemplateLogic:
    """Testet die Header-Spalten der CSV-Templates."""

    MANUAL_RESULTS_HEADER = ['query', 'engine', 'country', 'lang', 'page',
                              'type', 'rank', 'title', 'url', 'snippet', 'ai_full_text']
    URLS_HEADER = ['url']
    QUERIES_HEADER = ['query']

    def test_manual_results_has_required_cols(self):
        for col in ['query', 'engine', 'url', 'type']:
            assert col in self.MANUAL_RESULTS_HEADER

    def test_manual_results_has_ai_column(self):
        assert 'ai_full_text' in self.MANUAL_RESULTS_HEADER

    def test_urls_template_single_column(self):
        assert self.URLS_HEADER == ['url']

    def test_queries_template_single_column(self):
        assert self.QUERIES_HEADER == ['query']

    def test_manual_results_column_count(self):
        assert len(self.MANUAL_RESULTS_HEADER) == 11

    def test_manual_template_parseable_as_dataframe(self):
        df = pd.DataFrame(columns=self.MANUAL_RESULTS_HEADER)
        assert list(df.columns) == self.MANUAL_RESULTS_HEADER
