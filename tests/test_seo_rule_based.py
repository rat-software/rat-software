"""
Unit tests for seo_rule_based/libs/indicators.py and seo_rule_based.py

Covers: all pure-logic indicator functions, file-based indicator functions
        (micros, plugins, sources, keywords), and the main() orchestration.
"""
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Stub seleniumbase before any import touches it ───────────────────────────
_sb = types.ModuleType('seleniumbase')
_sb.Driver = type('Driver', (), {})
sys.modules.setdefault('seleniumbase', _sb)

# ── Path setup ───────────────────────────────────────────────────────────────
_CLASSIFIER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'classifier', 'classifiers', 'seo_rule_based',
)
_LIBS_DIR = os.path.join(_CLASSIFIER_DIR, 'libs')
sys.path.insert(0, _LIBS_DIR)
sys.path.insert(0, _CLASSIFIER_DIR)

# Stub lib_db / lib_helper so seo_rule_based.py can be imported
for _stub_name in ('lib_db', 'lib_helper'):
    if _stub_name not in sys.modules:
        _m = types.ModuleType(_stub_name)
        _m.DB = type('DB', (), {})
        _m.Helper = type('Helper', (), {})
        sys.modules[_stub_name] = _m

from indicators import (
    match_text,
    is_valid_url,
    get_scheme,
    get_netloc,
    get_hyperlinks,
    identify_url_length,
    identify_https,
    identify_og,
    identify_viewport,
    identify_sitemap,
    identify_wordpress,
    identify_canonical,
    identify_nofollow,
    identify_h1,
    identify_hyperlinks,
    identify_keywords_in_url,
    identify_keyword_density,
    identify_description,
    identify_title,
    identify_micros,
    identify_keywords_in_source,
    identify_plugins,
    identify_sources,
)


# ─────────────────────────────────────────────────────────────────────────────
# match_text
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchText(unittest.TestCase):

    def test_exact_match(self):
        self.assertTrue(match_text('hello world', 'hello world'))

    def test_star_wildcard_middle(self):
        self.assertTrue(match_text('hello test world', '*test*'))

    def test_no_match(self):
        self.assertFalse(match_text('hello world', 'goodbye'))

    def test_case_insensitive(self):
        self.assertTrue(match_text('Hello World', '*world*'))

    def test_leading_wildcard(self):
        self.assertTrue(match_text('test hello', '*hello'))

    def test_trailing_wildcard(self):
        self.assertTrue(match_text('hello test', 'hello*'))

    def test_empty_text_against_star(self):
        self.assertTrue(match_text('', '*'))

    def test_empty_pattern_only_matches_empty(self):
        self.assertTrue(match_text('', ''))
        self.assertFalse(match_text('x', ''))


# ─────────────────────────────────────────────────────────────────────────────
# is_valid_url
# ─────────────────────────────────────────────────────────────────────────────

class TestIsValidUrl(unittest.TestCase):

    def test_valid_https_url(self):
        self.assertTrue(is_valid_url('https://example.com'))

    def test_valid_http_url_with_path(self):
        self.assertTrue(is_valid_url('http://example.com/page'))

    def test_no_scheme_is_invalid(self):
        self.assertFalse(is_valid_url('example.com'))

    def test_scheme_only_no_netloc(self):
        self.assertFalse(is_valid_url('https://'))

    def test_empty_string(self):
        self.assertFalse(is_valid_url(''))

    def test_ftp_scheme_is_valid(self):
        self.assertTrue(is_valid_url('ftp://files.example.com'))


# ─────────────────────────────────────────────────────────────────────────────
# get_scheme / get_netloc
# ─────────────────────────────────────────────────────────────────────────────

class TestGetScheme(unittest.TestCase):

    def test_https(self):
        self.assertEqual(get_scheme('https://example.com'), 'https')

    def test_http(self):
        self.assertEqual(get_scheme('http://example.com'), 'http')

    def test_no_scheme_returns_empty(self):
        self.assertEqual(get_scheme('example.com'), '')


class TestGetNetloc(unittest.TestCase):

    def test_standard_domain(self):
        self.assertEqual(get_netloc('https://example.com/path'), 'example.com')

    def test_subdomain_preserved(self):
        self.assertEqual(get_netloc('https://www.example.com'), 'www.example.com')

    def test_with_port(self):
        self.assertEqual(get_netloc('https://example.com:8080/'), 'example.com:8080')

    def test_no_netloc_returns_empty(self):
        self.assertEqual(get_netloc('example.com'), '')


# ─────────────────────────────────────────────────────────────────────────────
# identify_url_length
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyUrlLength(unittest.TestCase):

    def test_https_stripped(self):
        # 'https://example.com' → 'example.com' → len 11
        self.assertEqual(identify_url_length('https://example.com'), '11')

    def test_http_stripped(self):
        self.assertEqual(identify_url_length('http://example.com'), '11')

    def test_www_stripped(self):
        # 'https://www.example.com' → remove www. → 'https://example.com' → remove https:// → 'example.com' → 11
        self.assertEqual(identify_url_length('https://www.example.com'), '11')

    def test_returns_string(self):
        self.assertIsInstance(identify_url_length('https://example.com'), str)

    def test_path_included_in_length(self):
        # 'https://example.com/page' → 'example.com/page' → len 16
        self.assertEqual(identify_url_length('https://example.com/page'), '16')


# ─────────────────────────────────────────────────────────────────────────────
# identify_https
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyHttps(unittest.TestCase):

    def test_https_returns_1(self):
        self.assertEqual(identify_https('https://example.com'), 1)

    def test_http_returns_0(self):
        self.assertEqual(identify_https('http://example.com'), 0)

    def test_ftp_returns_0(self):
        self.assertEqual(identify_https('ftp://example.com'), 0)

    def test_no_scheme_returns_0(self):
        self.assertEqual(identify_https('example.com'), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_og
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyOg(unittest.TestCase):

    def test_og_tag_present_returns_1(self):
        html = '<meta property="og:title" content="Test Page">'
        self.assertEqual(identify_og(html), 1)

    def test_og_description_present_returns_1(self):
        html = '<meta property="og:description" content="Desc">'
        self.assertEqual(identify_og(html), 1)

    def test_no_og_tag_returns_0(self):
        self.assertEqual(identify_og('<meta name="description" content="Test">'), 0)

    def test_empty_source_returns_0(self):
        self.assertEqual(identify_og(''), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_viewport
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyViewport(unittest.TestCase):

    def test_viewport_present_returns_1(self):
        html = '<meta name="viewport" content="width=device-width, initial-scale=1">'
        self.assertEqual(identify_viewport(html), 1)

    def test_no_viewport_returns_0(self):
        self.assertEqual(identify_viewport('<meta name="description" content="Test">'), 0)

    def test_empty_source_returns_0(self):
        self.assertEqual(identify_viewport(''), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_sitemap
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifySitemap(unittest.TestCase):

    def test_sitemap_link_present_returns_1(self):
        self.assertEqual(identify_sitemap('<a href="/sitemap.xml">Sitemap</a>'), 1)

    def test_sitemap_in_href_returns_1(self):
        self.assertEqual(identify_sitemap('<a href="https://example.com/sitemap">Map</a>'), 1)

    def test_no_sitemap_link_returns_0(self):
        self.assertEqual(identify_sitemap('<a href="/home">Home</a>'), 0)

    def test_empty_source_returns_0(self):
        self.assertEqual(identify_sitemap(''), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_wordpress
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyWordpress(unittest.TestCase):

    def test_wordpress_generator_returns_1(self):
        html = '<html><head><meta name="generator" content="WordPress 6.0"></head></html>'
        self.assertEqual(identify_wordpress(html), 1)

    def test_different_cms_returns_0(self):
        html = '<html><head><meta name="generator" content="Drupal 9.0"></head></html>'
        self.assertEqual(identify_wordpress(html), 0)

    def test_no_generator_returns_0(self):
        self.assertEqual(identify_wordpress('<html><head></head></html>'), 0)

    def test_wordpress_case_insensitive(self):
        html = '<html><head><meta name="generator" content="WORDPRESS 5.9"></head></html>'
        self.assertEqual(identify_wordpress(html), 1)


# ─────────────────────────────────────────────────────────────────────────────
# identify_canonical
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyCanonical(unittest.TestCase):

    def test_link_canonical_returns_1(self):
        html = '<html><head><link rel="canonical" href="https://example.com"></head></html>'
        self.assertEqual(identify_canonical(html), 1)

    def test_a_canonical_returns_1(self):
        html = '<a rel="canonical" href="https://example.com">Canonical</a>'
        self.assertEqual(identify_canonical(html), 1)

    def test_two_canonical_links_returns_2(self):
        html = ('<html><head>'
                '<link rel="canonical" href="https://example.com">'
                '<link rel="canonical" href="https://example.com/alt">'
                '</head></html>')
        self.assertEqual(identify_canonical(html), 2)

    def test_no_canonical_returns_0(self):
        html = '<html><head><link rel="stylesheet" href="style.css"></head></html>'
        self.assertEqual(identify_canonical(html), 0)

    def test_empty_source_returns_0(self):
        self.assertEqual(identify_canonical('<html></html>'), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_nofollow
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyNofollow(unittest.TestCase):

    def test_one_nofollow_link(self):
        html = '<a rel="nofollow" href="https://example.com">Link</a>'
        self.assertEqual(identify_nofollow(html), 1)

    def test_two_nofollow_links(self):
        html = ('<a rel="nofollow" href="https://a.com">A</a>'
                '<a rel="nofollow" href="https://b.com">B</a>')
        self.assertEqual(identify_nofollow(html), 2)

    def test_no_nofollow_returns_0(self):
        html = '<a href="https://example.com">Link</a>'
        self.assertEqual(identify_nofollow(html), 0)

    def test_regular_link_not_counted(self):
        html = '<a rel="follow" href="https://example.com">Link</a>'
        self.assertEqual(identify_nofollow(html), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_h1
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyH1(unittest.TestCase):

    def test_one_h1(self):
        self.assertEqual(identify_h1('<h1>Main Title</h1>'), 1)

    def test_two_h1_tags(self):
        self.assertEqual(identify_h1('<h1>A</h1><h1>B</h1>'), 2)

    def test_h2_not_counted(self):
        self.assertEqual(identify_h1('<h2>Subtitle</h2>'), 0)

    def test_no_headings_returns_0(self):
        self.assertEqual(identify_h1('<html><body><p>text</p></body></html>'), 0)


# ─────────────────────────────────────────────────────────────────────────────
# get_hyperlinks
# ─────────────────────────────────────────────────────────────────────────────

class TestGetHyperlinks(unittest.TestCase):

    def test_absolute_href_preserved(self):
        html = '<a href="https://other.com/page">Link</a>'
        result = get_hyperlinks(html, 'https://example.com')
        self.assertIn('https://other.com/page', result)
        self.assertIn('[url]', result)

    def test_relative_href_prefixed_with_main(self):
        html = '<a href="/about">About</a>'
        result = get_hyperlinks(html, 'https://example.com')
        self.assertIn('https://example.com', result)

    def test_error_source_returns_none(self):
        # get_hyperlinks returns None implicitly when source == 'error'
        result = get_hyperlinks('error', 'https://example.com')
        self.assertIsNone(result)

    def test_mailto_links_excluded(self):
        html = '<a href="mailto:test@example.com">Email</a>'
        result = get_hyperlinks(html, 'https://example.com')
        self.assertNotIn('mailto:', result)

    def test_no_links_returns_empty_string(self):
        html = '<html><body><p>No links here</p></body></html>'
        result = get_hyperlinks(html, 'https://example.com')
        self.assertEqual(result, '')


# ─────────────────────────────────────────────────────────────────────────────
# identify_hyperlinks
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyHyperlinks(unittest.TestCase):

    def test_internal_link_counted(self):
        hyperlinks = '[url]Home   https://example.com/home'
        result = identify_hyperlinks(hyperlinks, 'https://example.com')
        self.assertEqual(result['internal'], 1)
        self.assertEqual(result['external'], 0)

    def test_external_link_counted(self):
        hyperlinks = '[url]Other   https://other.com/page'
        result = identify_hyperlinks(hyperlinks, 'https://example.com')
        self.assertEqual(result['internal'], 0)
        self.assertEqual(result['external'], 1)

    def test_mixed_links(self):
        hyperlinks = (
            '[url]Home   https://example.com/home'
            '[url]Other   https://other.com/page'
            '[url]Also Internal   https://example.com/about'
        )
        result = identify_hyperlinks(hyperlinks, 'https://example.com')
        self.assertEqual(result['internal'], 2)
        self.assertEqual(result['external'], 1)

    def test_no_valid_links_returns_zeros(self):
        result = identify_hyperlinks('[url]Text   not-a-url', 'https://example.com')
        self.assertEqual(result['internal'], 0)
        self.assertEqual(result['external'], 0)

    def test_empty_hyperlinks_returns_zeros(self):
        result = identify_hyperlinks('', 'https://example.com')
        self.assertEqual(result['internal'], 0)
        self.assertEqual(result['external'], 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_keywords_in_url
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyKeywordsInUrl(unittest.TestCase):

    def test_both_keywords_in_url(self):
        url = 'https://example.com/seo-tools-guide'
        self.assertEqual(identify_keywords_in_url(url, 'seo tools'), 2)

    def test_one_keyword_in_url(self):
        url = 'https://example.com/seo-guide'
        self.assertEqual(identify_keywords_in_url(url, 'seo tools'), 1)

    def test_no_keywords_in_url(self):
        url = 'https://example.com/unrelated-page'
        self.assertEqual(identify_keywords_in_url(url, 'seo tools'), 0)

    def test_case_insensitive(self):
        url = 'https://example.com/SEO-Guide'
        self.assertEqual(identify_keywords_in_url(url, 'seo'), 1)

    def test_empty_query_returns_zero(self):
        self.assertEqual(identify_keywords_in_url('https://example.com/seo', ''), 0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_keyword_density
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyKeywordDensity(unittest.TestCase):

    def test_two_of_three_words_match(self):
        # 'seo' appears 2 times in 3 words → density = 66%
        html = '<html><body><p>seo seo test</p></body></html>'
        result = identify_keyword_density(html, 'seo')
        self.assertEqual(result, 66.0)

    def test_all_words_match(self):
        html = '<html><body><p>seo seo seo</p></body></html>'
        result = identify_keyword_density(html, 'seo')
        self.assertEqual(result, 100.0)

    def test_no_match_returns_zero(self):
        html = '<html><body><p>python python python</p></body></html>'
        result = identify_keyword_density(html, 'seo')
        self.assertEqual(result, 0.0)

    def test_empty_query_returns_none(self):
        html = '<html><body><p>some text</p></body></html>'
        self.assertIsNone(identify_keyword_density(html, ''))

    def test_script_content_excluded(self):
        html = '<html><body><p>word</p><script>seo seo seo seo</script></body></html>'
        result = identify_keyword_density(html, 'seo')
        self.assertEqual(result, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# identify_description
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyDescription(unittest.TestCase):

    def test_meta_description_present_returns_1(self):
        html = '<html><head><meta name="description" content="This is a description"></head></html>'
        self.assertEqual(identify_description(html), 1)

    def test_og_description_present_returns_1(self):
        html = '<html><head><meta property="og:description" content="OG Desc here"></head></html>'
        self.assertEqual(identify_description(html), 1)

    def test_no_description_returns_0(self):
        self.assertEqual(identify_description('<html><head></head></html>'), 0)

    def test_very_short_description_returns_0(self):
        # Content 'a' → str(['a']) = "['a']" → len 5, NOT > 5 → 0
        html = '<html><head><meta name="description" content="a"></head></html>'
        self.assertEqual(identify_description(html), 0)

    def test_two_char_description_returns_1(self):
        # Content 'ab' → str(['ab']) = "['ab']" → len 6 > 5 → 1
        html = '<html><head><meta name="description" content="ab"></head></html>'
        self.assertEqual(identify_description(html), 1)


# ─────────────────────────────────────────────────────────────────────────────
# identify_title
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyTitle(unittest.TestCase):

    def test_title_tag_present_returns_1(self):
        html = '<html><head><title>My Page Title</title></head></html>'
        self.assertEqual(identify_title(html), 1)

    def test_og_title_present_returns_1(self):
        html = '<html><head><meta property="og:title" content="OG Title"></head></html>'
        self.assertEqual(identify_title(html), 1)

    def test_no_title_returns_0(self):
        self.assertEqual(identify_title('<html><head></head></html>'), 0)

    def test_meta_title_present_returns_1(self):
        html = '<html><head><meta name="title" content="Meta Title"></head></html>'
        self.assertEqual(identify_title(html), 1)


# ─────────────────────────────────────────────────────────────────────────────
# identify_micros  (reads micro.csv — uses actual project file)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyMicros(unittest.TestCase):

    def test_json_ld_detected(self):
        html = '<script type="application/ld+json">{"@type": "Product"}</script>'
        result = identify_micros(html)
        self.assertIn('JSON-LD', result)

    def test_schema_org_detected(self):
        html = '<div itemscope itemtype="https://schema.org/Product">text</div>'
        result = identify_micros(html)
        self.assertIn('schema.org', result)

    def test_no_micros_returns_empty_list(self):
        result = identify_micros('<html><body><p>plain text</p></body></html>')
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])

    def test_returns_list(self):
        self.assertIsInstance(identify_micros('<html></html>'), list)


# ─────────────────────────────────────────────────────────────────────────────
# identify_keywords_in_source  (reads kw.ini — uses actual project file)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyKeywordsInSource(unittest.TestCase):

    def test_keyword_in_title_counted(self):
        html = '<html><head><title>SEO Tools Guide</title></head><body></body></html>'
        result = identify_keywords_in_source(html, 'seo')
        self.assertGreater(result, 0)

    def test_keyword_not_in_source_returns_zero(self):
        html = '<html><head><title>Unrelated Page</title></head><body><p>nothing here</p></body></html>'
        result = identify_keywords_in_source(html, 'zxqwerty123')
        self.assertEqual(result, 0)

    def test_multiple_keywords_counted(self):
        html = '<html><head><title>SEO Tools</title></head><body></body></html>'
        result_two = identify_keywords_in_source(html, 'seo tools')
        result_one = identify_keywords_in_source(html, 'seo')
        self.assertGreaterEqual(result_two, result_one)

    def test_returns_int(self):
        html = '<html><head><title>Test</title></head></html>'
        self.assertIsInstance(identify_keywords_in_source(html, 'test'), int)


# ─────────────────────────────────────────────────────────────────────────────
# identify_plugins  (reads evaluation.ini + CSVs — uses actual project files)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifyPlugins(unittest.TestCase):

    def test_returns_dict_with_expected_keys(self):
        result = identify_plugins('<html></html>')
        for key in ('tools analytics', 'tools seo', 'tools caching', 'tools social', 'tools ads'):
            self.assertIn(key, result)

    def test_each_value_is_list(self):
        result = identify_plugins('<html></html>')
        for value in result.values():
            self.assertIsInstance(value, list)

    def test_no_tools_in_plain_html(self):
        result = identify_plugins('<html><body><p>plain text</p></body></html>')
        for value in result.values():
            self.assertEqual(value, [])

    def test_matomo_analytics_detected(self):
        html = '<script>g.src=u+matomo.js</script>'
        result = identify_plugins(html)
        self.assertIn('Matomo', result.get('tools analytics', []))

    def test_yoast_seo_detected(self):
        html = '<!-- https://yoast.com/wordpress/plugins/seo/ -- Yoast SEO -->'
        result = identify_plugins(html)
        self.assertIn('Yoast SEO Plugin', result.get('tools seo', []))


# ─────────────────────────────────────────────────────────────────────────────
# identify_sources  (reads sources.ini + CSVs — uses actual project files)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifySources(unittest.TestCase):

    def test_returns_dict_with_expected_keys(self):
        result = identify_sources('https://example.com')
        for key in ('ads', 'company', 'seo_customers', 'news', 'not_optimized',
                    'search_engine_services', 'shops'):
            self.assertIn(key, result)

    def test_each_value_is_list(self):
        result = identify_sources('https://example.com')
        for value in result.values():
            self.assertIsInstance(value, list)

    def test_unknown_url_all_empty(self):
        result = identify_sources('https://this-domain-is-not-in-any-list-xyz123.example')
        for value in result.values():
            self.assertEqual(value, [])

    def test_wikipedia_classified_as_not_optimized(self):
        result = identify_sources('https://de.wikipedia.org/wiki/Test')
        self.assertTrue(len(result['not_optimized']) > 0)

    def test_news_site_classified_as_news(self):
        result = identify_sources('https://www.t-online.de/news/article')
        self.assertTrue(len(result['news']) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# main() — orchestration
# ─────────────────────────────────────────────────────────────────────────────

class TestMainOrchestration(unittest.TestCase):
    """
    Tests for main() in seo_rule_based.py.  db and helper are MagicMocks.
    Selenium-dependent functions (calculate_loading_time, identify_robots_txt)
    are patched in the seo_rule_based module namespace.
    """

    def _make_result(self, **overrides):
        base = {
            'id': 1, 'source': 10, 'file_path': '/fake/path',
            'status_code': 200, 'error_code': None,
            'url': 'https://example.com', 'main': 'https://example.com',
            'query': 'test',
        }
        base.update(overrides)
        return base

    def _run(self, results, sources_duplicates=None, code=None):
        import seo_rule_based as rb
        db = MagicMock()
        db.get_results.return_value = results
        db.check_classification_result_not_in_process.return_value = False
        db.check_classification_result.return_value = None
        db.check_source_duplicates.return_value = sources_duplicates or []
        helper = MagicMock()
        if code is not None:
            helper.decode_code.return_value = code
        rb.main(classifier_id=1, db=db, helper=helper, job_server='test', study_id=42)
        return db, helper

    # ── Empty / skipped results ───────────────────────────────────────────────

    def test_empty_results_does_nothing(self):
        db, _ = self._run([])
        db.insert_classification_result.assert_not_called()

    def test_already_processed_result_is_skipped(self):
        import seo_rule_based as rb
        db = MagicMock()
        db.get_results.return_value = [self._make_result()]
        db.check_classification_result_not_in_process.return_value = True
        rb.main(1, db, MagicMock(), 'test', 42)
        db.insert_classification_result.assert_not_called()

    def test_result_being_processed_by_another_server_is_skipped(self):
        import seo_rule_based as rb
        db = MagicMock()
        db.get_results.return_value = [self._make_result()]
        db.check_classification_result_not_in_process.return_value = False
        db.check_classification_result.return_value = 'in process'
        rb.main(1, db, MagicMock(), 'test', 42)
        db.insert_classification_result.assert_not_called()

    # ── In-process marker ────────────────────────────────────────────────────

    def test_in_process_marker_inserted(self):
        db, _ = self._run([self._make_result()], sources_duplicates=[])
        db.insert_classification_result.assert_called_with(1, 'in process', 1, 'test')

    # ── No-duplicate path: classification block not entered ──────────────────

    def test_no_duplicates_update_not_called(self):
        # sources_duplicates = [] → len = 0 → check_for_duplicates returns False
        # → classification block never entered → update never called
        db, _ = self._run([self._make_result()], sources_duplicates=[])
        db.update_classification_result.assert_not_called()

    # ── Full classification path (via duplicate gate) ────────────────────────

    @patch('seo_rule_based.calculate_loading_time', return_value=2.0)
    @patch('seo_rule_based.identify_robots_txt', return_value=0)
    def test_status_not_200_writes_error(self, _robots, _loading):
        import seo_rule_based as rb
        result = self._make_result(status_code=404, error_code=None)
        db = MagicMock()
        db.get_results.return_value = [result]
        db.check_classification_result_not_in_process.return_value = False
        db.check_classification_result.return_value = None
        db.check_source_duplicates.return_value = ['dup1', 'dup2']
        db.get_results_result_source.return_value = [(1,)]
        db.get_classifier_result.return_value = [('some_result',)]
        db.get_indicators.return_value = []

        helper = MagicMock()
        helper.decode_code.return_value = '<html><head><title>T</title></head></html>'
        rb.main(1, db, helper, 'test', 42)

        db.update_classification_result.assert_called()
        self.assertEqual(db.update_classification_result.call_args[0][0], 'error')

    @patch('seo_rule_based.calculate_loading_time', return_value=2.0)
    @patch('seo_rule_based.identify_robots_txt', return_value=1)
    def test_valid_result_produces_classification(self, _robots, _loading):
        import seo_rule_based as rb
        html = ('<html><head><title>SEO Page</title>'
                '<meta name="description" content="Good description text here">'
                '<meta name="viewport" content="width=device-width">'
                '</head><body><h1>SEO</h1></body></html>')
        result = self._make_result()
        db = MagicMock()
        db.get_results.return_value = [result]
        db.check_classification_result_not_in_process.return_value = False
        db.check_classification_result.return_value = None
        db.check_source_duplicates.return_value = ['dup1', 'dup2']
        db.get_results_result_source.return_value = [(1,)]
        db.get_classifier_result.return_value = [('some_result',)]
        db.get_indicators.return_value = []

        helper = MagicMock()
        helper.decode_code.return_value = html
        rb.main(1, db, helper, 'test', 42)

        # update is called once for the duplicate copy and once for this result
        self.assertGreaterEqual(db.update_classification_result.call_count, 1)
        last_call_arg = db.update_classification_result.call_args_list[-1][0][0]
        self.assertIn(last_call_arg, [
            'most_probably_optimized', 'probably_optimized',
            'probably_not_optimized', 'most_probably_not_optimized',
            'uncertain', 'error',
        ])

    @patch('seo_rule_based.calculate_loading_time', return_value=2.0)
    @patch('seo_rule_based.identify_robots_txt', return_value=0)
    def test_exception_writes_error(self, _robots, _loading):
        import seo_rule_based as rb
        result = self._make_result()
        db = MagicMock()
        db.get_results.return_value = [result]
        db.check_classification_result_not_in_process.return_value = False
        db.check_classification_result.return_value = None
        db.check_source_duplicates.return_value = ['dup1', 'dup2']
        db.get_results_result_source.return_value = [(1,)]
        db.get_classifier_result.return_value = [('some_result',)]
        db.get_indicators.return_value = []

        helper = MagicMock()
        helper.decode_code.side_effect = RuntimeError("disk error")
        rb.main(1, db, helper, 'test', 42)

        # last call is the classification error for this result
        self.assertGreaterEqual(db.update_classification_result.call_count, 1)
        last_call_arg = db.update_classification_result.call_args_list[-1][0][0]
        self.assertEqual(last_call_arg, 'error')


if __name__ == '__main__':
    unittest.main()
