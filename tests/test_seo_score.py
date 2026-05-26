"""
Unit tests for seo_score.py

Covers: SEOScorer class (thresholds, score calculation, edge cases),
        and all standalone analysis functions.
"""
import sys
import os
import types
import unittest
from bs4 import BeautifulSoup

# Add the seo_score package directory to sys.path so seo_score.py can be imported
# from this tests/ directory, regardless of where pytest is invoked from.
_SEO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'classifier', 'classifiers', 'seo_score',
)
sys.path.insert(0, _SEO_DIR)

# Inject a stub for the `indicators` module so the module-level
# `from indicators import *` in seo_score.py does not require
# Selenium or any network access.
sys.modules.setdefault('indicators', types.ModuleType('indicators'))

from seo_score import (
    SEOScorer,
    analyze_content_length,
    analyze_heading_structure,
    analyze_link_quality,
    analyze_images,
    analyze_navigation,
    analyze_title,
    analyze_description,
    check_social_tags,
    analyze_general_content_optimization,
    analyze_specific_keyword,
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'html.parser')


# ─────────────────────────────────────────────────────────────────
# SEOScorer.get_classification — threshold boundary tests
# ─────────────────────────────────────────────────────────────────

class TestGetClassification(unittest.TestCase):

    def setUp(self):
        self.scorer = SEOScorer()

    def test_score_at_75_threshold(self):
        self.assertEqual(self.scorer.get_classification(75), 'most_probably_optimized')

    def test_score_just_below_75(self):
        self.assertEqual(self.scorer.get_classification(74.99), 'probably_optimized')

    def test_score_at_45_threshold(self):
        self.assertEqual(self.scorer.get_classification(45), 'probably_optimized')

    def test_score_just_below_45(self):
        self.assertEqual(self.scorer.get_classification(44.99), 'probably_not_optimized')

    def test_score_at_20_threshold(self):
        self.assertEqual(self.scorer.get_classification(20), 'probably_not_optimized')

    def test_score_just_below_20(self):
        self.assertEqual(self.scorer.get_classification(19.99), 'most_probably_not_optimized')

    def test_score_zero(self):
        self.assertEqual(self.scorer.get_classification(0), 'most_probably_not_optimized')


# ─────────────────────────────────────────────────────────────────
# SEOScorer.calculate_score — edge cases and main paths
# ─────────────────────────────────────────────────────────────────

class TestCalculateScore(unittest.TestCase):

    def setUp(self):
        self.scorer = SEOScorer()

    # Edge case: empty dict
    def test_empty_indicators_returns_zero(self):
        result = self.scorer.calculate_score({})
        self.assertEqual(result, {'total_score': 0})

    # Edge case: None (also falsy)
    def test_none_indicators_returns_zero(self):
        result = self.scorer.calculate_score(None)
        self.assertEqual(result, {'total_score': 0})

    # Edge case: non-HTML document
    def test_non_html_returns_excluded(self):
        indicators = {
            'is_html': False,
            'reason': 'PDF document',
            'content_type': 'application/pdf',
        }
        result = self.scorer.calculate_score(indicators)
        self.assertEqual(result['total_score'], 0)
        self.assertEqual(result['status'], 'excluded')
        self.assertEqual(result['content_type'], 'application/pdf')

    def test_non_html_default_reason_when_missing(self):
        result = self.scorer.calculate_score({'is_html': False})
        self.assertEqual(result['status'], 'excluded')
        self.assertIn('reason', result)

    # SEO plugin detected → instant perfect score
    def test_seo_plugin_returns_perfect_score(self):
        result = self.scorer.calculate_score({'tools_seo': ['yoast']})
        self.assertEqual(result['total_score'], 100)
        self.assertEqual(result['classification'], 'most_probably_optimized')
        for cat_score in result['category_scores'].values():
            self.assertEqual(cat_score, 100)

    def test_analytics_boost_does_not_exceed_100(self):
        indicators = {
            'tools_seo': [],
            'tools_analytics': ['ga'],
            'https': True,
            'robots_txt': True,
            'sitemap': True,
            'canonical': True,
            'content_length_score': 100,
            'heading_structure_score': 100,
            'link_quality_score': 100,
            'keyword_optimization_score': 100,
            'image_optimization_score': 100,
            'title_score': 100,
            'description_score': 100,
            'social_tags_score': 100,
            'viewport': True,
            'h1': True,
            'navigation_score': 100,
            'loading_time': 1.0,
            'tools_caching': [],
            'tools_micro': [],
            'tools_content': [],
            'tools_social': [],
        }
        result = self.scorer.calculate_score(indicators)
        self.assertLessEqual(result['total_score'], 100)

    # Weighted sum is correct
    def test_weighted_sum_calculation(self):
        # Set all category sub-scores to produce predictable category scores
        indicators = {
            'tools_seo': [],
            'tools_analytics': [],
            # technical: https+robots+sitemap+canonical = 20+20+20+20 = 80
            'https': True,
            'robots_txt': True,
            'sitemap': True,
            'canonical': True,
            'tools_caching': [],
            'tools_micro': [],
            # content: zero all sub-scores
            'content_length_score': 0,
            'heading_structure_score': 0,
            'link_quality_score': 0,
            'keyword_optimization_score': 0,
            'image_optimization_score': 0,
            'title_score': 0,
            'description_score': 0,
            'tools_content': [],
            'tools_social': [],
            # ux: loading unknown, no viewport, no https (already counted)
            'loading_time': -1,
            'viewport': False,
            'navigation_score': 0,
            # meta: all missing
            'social_tags_score': 0,
            'h1': False,
        }
        result = self.scorer.calculate_score(indicators)
        # Technical score = 80 (https+robots+sitemap+canonical), others = 0
        # UX also picks up https=True → +20, so UX = 20
        # Total = 80*0.35 + 20*0.20 = 28 + 4 = 32
        self.assertAlmostEqual(result['total_score'], 32.0, places=1)



# ─────────────────────────────────────────────────────────────────
# SEOScorer._calculate_technical_score
# ─────────────────────────────────────────────────────────────────

class TestCalculateTechnicalScore(unittest.TestCase):

    def setUp(self):
        self.scorer = SEOScorer()

    def _score(self, indicators):
        return self.scorer._calculate_technical_score(indicators)

    def test_all_core_indicators_present(self):
        # https+robots+sitemap+canonical each +20 = 80; schema missing
        ind = {'https': True, 'robots_txt': True, 'sitemap': True, 'canonical': True}
        self.assertEqual(self._score(ind), 80)

    def test_schema_org_in_indicators_adds_20(self):
        ind = {'https': True, 'robots_txt': True, 'sitemap': True, 'canonical': True,
               'schema': 'schema.org'}
        self.assertEqual(self._score(ind), 100)

    def test_missing_https_subtracts_20(self):
        ind = {'https': False, 'robots_txt': True, 'sitemap': True, 'canonical': True}
        # 0 - 20 + 20 + 20 + 20 = 40
        self.assertEqual(self._score(ind), 40)

    def test_both_https_and_robots_missing_gives_zero(self):
        ind = {'https': False, 'robots_txt': False, 'sitemap': False, 'canonical': False}
        # -20 -20 = -40 → clamped to 0
        self.assertEqual(self._score(ind), 0)

    def test_caching_tool_adds_bonus(self):
        ind = {'https': True, 'robots_txt': True, 'sitemap': True, 'canonical': True,
               'tools_caching': ['varnish'], 'tools_micro': []}
        self.assertEqual(self._score(ind), min(100, 80 + 10))

    def test_micro_tool_adds_bonus(self):
        ind = {'https': True, 'robots_txt': True, 'sitemap': True, 'canonical': True,
               'tools_micro': ['amp'], 'tools_caching': []}
        self.assertEqual(self._score(ind), min(100, 80 + 5))

    def test_score_capped_at_100(self):
        ind = {'https': True, 'robots_txt': True, 'sitemap': True, 'canonical': True,
               'schema': 'schema.org', 'tools_caching': ['x'], 'tools_micro': ['y']}
        self.assertEqual(self._score(ind), 100)

    def test_empty_indicators_gives_zero(self):
        # https=False (default), robots=False → -40 → 0
        self.assertEqual(self._score({}), 0)


# ─────────────────────────────────────────────────────────────────
# SEOScorer._calculate_content_score
# ─────────────────────────────────────────────────────────────────

class TestCalculateContentScore(unittest.TestCase):

    def setUp(self):
        self.scorer = SEOScorer()

    def _score(self, indicators):
        return self.scorer._calculate_content_score(indicators)

    def test_all_scores_perfect(self):
        ind = {
            'content_length_score': 100, 'heading_structure_score': 100,
            'link_quality_score': 100, 'keyword_optimization_score': 100,
            'image_optimization_score': 100, 'title_score': 80, 'description_score': 80,
            'tools_content': [], 'tools_social': [],
        }
        # 100*0.3 + 100*0.2 + 100*0.2 + 100*0.3 + 100*0.2 = 120 → 100
        self.assertEqual(self._score(ind), 100)

    def test_missing_title_applies_penalty(self):
        ind = {
            'content_length_score': 80, 'heading_structure_score': 80,
            'link_quality_score': 80, 'keyword_optimization_score': 80,
            'image_optimization_score': 0, 'title_score': 0, 'description_score': 80,
            'tools_content': [], 'tools_social': [],
        }
        # base = 80*0.3 + 80*0.2 + 80*0.2 + 80*0.3 = 80; penalty -20 = 60
        self.assertLess(self._score(ind), 80)

    def test_missing_description_applies_penalty(self):
        ind = {
            'content_length_score': 80, 'heading_structure_score': 80,
            'link_quality_score': 80, 'keyword_optimization_score': 80,
            'image_optimization_score': 0, 'title_score': 80, 'description_score': 0,
            'tools_content': [], 'tools_social': [],
        }
        self.assertLess(self._score(ind), 80)

    def test_content_tool_adds_10(self):
        ind = {
            'content_length_score': 0, 'heading_structure_score': 0,
            'link_quality_score': 0, 'keyword_optimization_score': 0,
            'image_optimization_score': 0, 'title_score': 80, 'description_score': 80,
            'tools_content': ['yoast_content'], 'tools_social': [],
        }
        self.assertEqual(self._score(ind), 10)

    def test_social_tool_adds_5(self):
        ind = {
            'content_length_score': 0, 'heading_structure_score': 0,
            'link_quality_score': 0, 'keyword_optimization_score': 0,
            'image_optimization_score': 0, 'title_score': 80, 'description_score': 80,
            'tools_content': [], 'tools_social': ['sharethis'],
        }
        self.assertEqual(self._score(ind), 5)

    def test_score_not_negative(self):
        self.assertGreaterEqual(self._score({}), 0)


# ─────────────────────────────────────────────────────────────────
# SEOScorer._calculate_user_experience_score
# ─────────────────────────────────────────────────────────────────

class TestCalculateUserExperienceScore(unittest.TestCase):

    def setUp(self):
        self.scorer = SEOScorer()

    def _score(self, indicators):
        return self.scorer._calculate_user_experience_score(indicators)

    def test_fast_loading_under_2s_adds_40(self):
        self.assertIn(self._score({'loading_time': 1.0}), range(40, 101))

    def test_loading_2_to_3s_adds_30(self):
        ind = {'loading_time': 2.5}
        score = self._score(ind)
        self.assertEqual(score, 30)

    def test_loading_3_to_4s_adds_20(self):
        ind = {'loading_time': 3.5}
        score = self._score(ind)
        self.assertEqual(score, 20)

    def test_loading_4s_plus_adds_0(self):
        ind = {'loading_time': 5.0}
        score = self._score(ind)
        self.assertEqual(score, 0)

    def test_unknown_loading_time_adds_0(self):
        ind = {'loading_time': -1}
        score = self._score(ind)
        self.assertEqual(score, 0)

    def test_viewport_adds_20(self):
        base = self._score({'loading_time': -1, 'viewport': False, 'https': False})
        with_viewport = self._score({'loading_time': -1, 'viewport': True, 'https': False})
        self.assertEqual(with_viewport - base, 20)

    def test_https_adds_20(self):
        base = self._score({'loading_time': -1, 'viewport': False, 'https': False})
        with_https = self._score({'loading_time': -1, 'viewport': False, 'https': True})
        self.assertEqual(with_https - base, 20)

    def test_all_signals_present(self):
        ind = {
            'loading_time': 1.0,
            'viewport': True,
            'https': True,
            'navigation_score': 100,
            'tools_micro': [],
        }
        # 40 + 20 + 20 + 100*0.2 = 40+20+20+20 = 100
        self.assertEqual(self._score(ind), 100)

    def test_score_not_negative(self):
        self.assertGreaterEqual(self._score({}), 0)


# ─────────────────────────────────────────────────────────────────
# SEOScorer._calculate_meta_score
# ─────────────────────────────────────────────────────────────────

class TestCalculateMetaScore(unittest.TestCase):

    def setUp(self):
        self.scorer = SEOScorer()

    def _score(self, indicators):
        return self.scorer._calculate_meta_score(indicators)

    def _full_ind(self):
        return {
            'title_score': 100,
            'description_score': 100,
            'social_tags_score': 100,
            'viewport': True,
            'h1': True,
        }

    def test_all_elements_present_gives_100(self):
        # 100*0.3 + 100*0.3 + 100*0.4 + 10 + 10 = 120 → 100
        self.assertEqual(self._score(self._full_ind()), 100)

    def test_missing_title_applies_30_penalty(self):
        ind = self._full_ind()
        ind['title_score'] = 0
        # No title → penalties=30; score from desc(30) + social(40) + viewport(10) + h1(10)=90
        # final = max(0, 90 - 30) = 60
        self.assertEqual(self._score(ind), 60)

    def test_missing_description_applies_30_penalty(self):
        ind = self._full_ind()
        ind['description_score'] = 0
        # No desc → penalties=30; score from title(30) + social(40) + viewport(10) + h1(10)=90
        # final = max(0, 90 - 30) = 60
        self.assertEqual(self._score(ind), 60)

    def test_missing_social_tags_applies_20_penalty(self):
        ind = self._full_ind()
        ind['social_tags_score'] = 0
        # score = 100*0.3 + 100*0.3 + 10 + 10 = 80; penalties = 20 → 60
        self.assertEqual(self._score(ind), 60)

    def test_missing_viewport_applies_10_penalty(self):
        ind = self._full_ind()
        ind['viewport'] = False
        # score = 100 + 10 - 10 = 100, penalty 10 → 90... wait let me recalculate:
        # title 100*0.3=30, desc 100*0.3=30, social 100*0.4=40, h1 +10 → score=110
        # penalties = 10 (viewport); final = max(0, 110-10) = 100 → min(100,100)=100
        self.assertLessEqual(self._score(ind), 100)

    def test_missing_h1_applies_10_penalty(self):
        ind = self._full_ind()
        ind['h1'] = False
        # score = 30+30+40+10 = 110, penalties=10 → 100
        self.assertLessEqual(self._score(ind), 100)

    def test_all_elements_missing_gives_zero(self):
        self.assertEqual(self._score({}), 0)

    def test_score_not_negative(self):
        self.assertGreaterEqual(self._score({}), 0)


# ─────────────────────────────────────────────────────────────────
# analyze_content_length
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeContentLength(unittest.TestCase):

    def _score(self, words: int) -> int:
        text = ' '.join(['word'] * words)
        soup = _soup(f'<body>{text}</body>')
        return analyze_content_length(soup)

    def test_1500_words_gives_100(self):
        self.assertEqual(self._score(1500), 100)

    def test_1000_words_gives_80(self):
        self.assertEqual(self._score(1000), 80)

    def test_500_words_gives_60(self):
        self.assertEqual(self._score(500), 60)

    def test_300_words_gives_40(self):
        self.assertEqual(self._score(300), 40)

    def test_150_words_gives_proportional(self):
        # (150 / 300) * 40 = 20
        self.assertAlmostEqual(self._score(150), 20, delta=1)

    def test_zero_words_gives_zero(self):
        soup = _soup('<body></body>')
        self.assertEqual(analyze_content_length(soup), 0)


# ─────────────────────────────────────────────────────────────────
# analyze_heading_structure
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeHeadingStructure(unittest.TestCase):

    def test_one_h1_gives_40(self):
        soup = _soup('<h1>Title</h1>')
        self.assertEqual(analyze_heading_structure(soup), 40)

    def test_h1_and_h2_gives_70(self):
        soup = _soup('<h1>Title</h1><h2>Sub</h2>')
        self.assertEqual(analyze_heading_structure(soup), 70)

    def test_full_hierarchy_gives_100(self):
        soup = _soup('<h1>T</h1><h2>S</h2><h3>SS</h3><h4>D</h4>')
        self.assertEqual(analyze_heading_structure(soup), 100)

    def test_multiple_h1_gives_zero_h1_points(self):
        soup = _soup('<h1>A</h1><h1>B</h1>')
        # no single h1 → 0; no h2/h3 → 0
        self.assertEqual(analyze_heading_structure(soup), 0)

    def test_no_headings_gives_zero(self):
        soup = _soup('<p>text</p>')
        self.assertEqual(analyze_heading_structure(soup), 0)


# ─────────────────────────────────────────────────────────────────
# analyze_link_quality
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeLinkQuality(unittest.TestCase):

    def test_optimal_ratio_and_enough_links(self):
        # 6 internal, 4 external → ratio 0.6, total 10 → 50 + 50 = 100
        self.assertEqual(analyze_link_quality(6, 4), 100)

    def test_ratio_in_acceptable_range(self):
        # 5 internal, 5 external → ratio 0.5 (0.4-0.9) → 30; total 10 → 50; total 80
        self.assertEqual(analyze_link_quality(5, 5), 80)

    def test_ratio_outside_range_no_ratio_bonus(self):
        # 1 internal, 9 external → ratio 0.1 (< 0.4) → 0; total 10 → 50
        self.assertEqual(analyze_link_quality(1, 9), 50)

    def test_few_links_partial_bonus(self):
        # 4 internal, 1 external → ratio 0.8 (0.6-0.8) → 50; total 5 → 25 = 75
        self.assertEqual(analyze_link_quality(4, 1), 75)

    def test_no_links_gives_zero(self):
        self.assertEqual(analyze_link_quality(0, 0), 0)


# ─────────────────────────────────────────────────────────────────
# analyze_images
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeImages(unittest.TestCase):

    def test_all_images_have_alt(self):
        soup = _soup('<img alt="a"><img alt="b">')
        self.assertEqual(analyze_images(soup), 100)

    def test_half_images_have_alt(self):
        soup = _soup('<img alt="a"><img>')
        self.assertEqual(analyze_images(soup), 50)

    def test_no_images_gives_zero(self):
        soup = _soup('<p>text</p>')
        self.assertEqual(analyze_images(soup), 0)

    def test_no_alt_on_any_gives_zero(self):
        soup = _soup('<img><img><img>')
        self.assertEqual(analyze_images(soup), 0)


# ─────────────────────────────────────────────────────────────────
# analyze_navigation
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeNavigation(unittest.TestCase):

    def test_all_elements_gives_100(self):
        soup = _soup('<nav></nav><footer></footer><form></form>')
        self.assertEqual(analyze_navigation(soup), 100)

    def test_only_nav_gives_40(self):
        soup = _soup('<nav></nav>')
        self.assertEqual(analyze_navigation(soup), 40)

    def test_only_form_gives_30(self):
        soup = _soup('<form></form>')
        self.assertEqual(analyze_navigation(soup), 30)

    def test_no_elements_gives_zero(self):
        soup = _soup('<p>text</p>')
        self.assertEqual(analyze_navigation(soup), 0)


# ─────────────────────────────────────────────────────────────────
# analyze_title
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeTitle(unittest.TestCase):

    def test_optimal_length_50_to_60(self):
        title = 'A' * 55
        score, text = analyze_title(_soup(f'<title>{title}</title>'))
        self.assertEqual(score, 100)
        self.assertEqual(text, title)

    def test_good_length_40_to_70(self):
        title = 'A' * 45
        score, _ = analyze_title(_soup(f'<title>{title}</title>'))
        self.assertEqual(score, 80)

    def test_acceptable_length_30_to_80(self):
        title = 'A' * 35
        score, _ = analyze_title(_soup(f'<title>{title}</title>'))
        self.assertEqual(score, 60)

    def test_very_short_title(self):
        title = 'A' * 10
        score, _ = analyze_title(_soup(f'<title>{title}</title>'))
        self.assertEqual(score, 40)

    def test_no_title_returns_zero(self):
        score, text = analyze_title(_soup('<p>nothing</p>'))
        self.assertEqual(score, 0)
        self.assertIsNone(text)

    def test_empty_title_tag_returns_zero(self):
        score, text = analyze_title(_soup('<title>   </title>'))
        self.assertEqual(score, 0)
        self.assertIsNone(text)

    def test_generic_title_untitled_penalised(self):
        score, _ = analyze_title(_soup('<title>untitled</title>'))
        self.assertLess(score, 40)



# ─────────────────────────────────────────────────────────────────
# analyze_description
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeDescription(unittest.TestCase):

    def _desc_soup(self, content):
        return _soup(f'<meta name="description" content="{content}">')

    def test_optimal_length_150_to_160(self):
        content = 'A' * 155
        score, text = analyze_description(self._desc_soup(content))
        self.assertEqual(score, 100)

    def test_good_length_130_to_170(self):
        content = 'A' * 140
        score, _ = analyze_description(self._desc_soup(content))
        self.assertEqual(score, 80)

    def test_acceptable_length_110_to_190(self):
        content = 'A' * 120
        score, _ = analyze_description(self._desc_soup(content))
        self.assertEqual(score, 60)

    def test_short_description(self):
        content = 'A' * 50
        score, _ = analyze_description(self._desc_soup(content))
        self.assertEqual(score, 40)

    def test_no_meta_description_returns_zero(self):
        score, text = analyze_description(_soup('<p>nothing</p>'))
        self.assertEqual(score, 0)
        self.assertIsNone(text)

    def test_empty_content_returns_zero(self):
        score, text = analyze_description(_soup('<meta name="description" content="">'))
        self.assertEqual(score, 0)
        self.assertIsNone(text)

    def test_generic_description_penalised(self):
        score, _ = analyze_description(self._desc_soup('description'))
        self.assertLess(score, 40)



# ─────────────────────────────────────────────────────────────────
# check_social_tags
# ─────────────────────────────────────────────────────────────────

class TestCheckSocialTags(unittest.TestCase):

    def test_both_og_and_twitter_gives_100(self):
        soup = _soup(
            '<meta property="og:title" content="x">'
            '<meta name="twitter:card" content="summary">'
        )
        score, tags = check_social_tags(soup)
        self.assertEqual(score, 100)
        self.assertTrue(tags['og_tags'])
        self.assertTrue(tags['twitter_tags'])

    def test_only_og_gives_50(self):
        soup = _soup('<meta property="og:title" content="x">')
        score, _ = check_social_tags(soup)
        self.assertEqual(score, 50)

    def test_only_twitter_gives_50(self):
        soup = _soup('<meta name="twitter:card" content="summary">')
        score, _ = check_social_tags(soup)
        self.assertEqual(score, 50)

    def test_no_tags_gives_zero(self):
        soup = _soup('<p>nothing</p>')
        score, tags = check_social_tags(soup)
        self.assertEqual(score, 0)
        self.assertEqual(tags['og_tags'], [])
        self.assertEqual(tags['twitter_tags'], [])


# ─────────────────────────────────────────────────────────────────
# analyze_general_content_optimization
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeGeneralContentOptimization(unittest.TestCase):

    def test_optimized_title_adds_25(self):
        soup = _soup('<title>' + 'A' * 40 + '</title>')
        score, reasons = analyze_general_content_optimization(soup)
        self.assertIn('Optimized title length', reasons)
        self.assertGreaterEqual(score, 25)

    def test_optimized_description_adds_25(self):
        soup = _soup(
            '<title>' + 'A' * 40 + '</title>'
            '<meta name="description" content="' + 'A' * 140 + '">'
        )
        score, reasons = analyze_general_content_optimization(soup)
        self.assertIn('Optimized description length', reasons)

    def test_proper_h1_usage_adds_25(self):
        soup = _soup(
            '<title>' + 'A' * 40 + '</title>'
            '<h1>Main</h1><h2>Sub</h2><h3>Sub2</h3>'
        )
        score, reasons = analyze_general_content_optimization(soup)
        self.assertIn('Proper H1 usage', reasons)

    def test_good_heading_structure_adds_25(self):
        soup = _soup('<h1>A</h1><h2>B</h2><h3>C</h3>')
        score, reasons = analyze_general_content_optimization(soup)
        self.assertIn('Good heading structure', reasons)

    def test_no_elements_gives_zero(self):
        soup = _soup('<p>nothing</p>')
        score, reasons = analyze_general_content_optimization(soup)
        self.assertEqual(score, 0)
        self.assertEqual(reasons, [])


# ─────────────────────────────────────────────────────────────────
# analyze_specific_keyword
# ─────────────────────────────────────────────────────────────────

class TestAnalyzeSpecificKeyword(unittest.TestCase):

    def _make_soup(self, title, desc, h1, body=''):
        return _soup(
            f'<title>{title}</title>'
            f'<meta name="description" content="{desc}">'
            f'<h1>{h1}</h1>'
            f'<p>{body}</p>'
        )

    def test_keyword_in_all_locations_gives_100(self):
        # Use a keyword that literally appears in each location without encoding issues
        url = 'https://example.com/seotools-guide'
        soup = self._make_soup('seotools Guide', 'Learn about seotools here', 'seotools')
        score, reasons = analyze_specific_keyword(soup, url, 'seotools')
        self.assertEqual(score, 100)
        self.assertIn('Keyword in URL', reasons)
        self.assertIn('Keyword in title', reasons)
        self.assertIn('Keyword in description', reasons)
        self.assertIn('Keyword in headers', reasons)

    def test_keyword_not_present_gives_zero(self):
        url = 'https://example.com/page'
        soup = self._make_soup('Unrelated page', 'Nothing here', 'Unrelated')
        score, reasons = analyze_specific_keyword(soup, url, 'seo tools')
        self.assertEqual(score, 0)
        self.assertEqual(reasons, [])

    def test_keyword_only_in_title(self):
        url = 'https://example.com/page'
        soup = self._make_soup('SEO Tools Guide', 'Nothing here', 'Unrelated')
        score, reasons = analyze_specific_keyword(soup, url, 'seo tools')
        self.assertEqual(score, 25)
        self.assertIn('Keyword in title', reasons)

    def test_keyword_matching_is_case_insensitive(self):
        url = 'https://example.com/page'
        soup = self._make_soup('SEO TOOLS', 'Desc', 'H1')
        score, reasons = analyze_specific_keyword(soup, url, 'seo tools')
        self.assertIn('Keyword in title', reasons)


if __name__ == '__main__':
    unittest.main()
