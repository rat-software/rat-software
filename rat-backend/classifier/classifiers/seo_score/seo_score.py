"""
The `main` function orchestrates the classification process for a classifier by checking for
duplicates, classifying results, and updating the database with classification information.

:param classifier_id: The `classifier_id` is a unique identifier for a specific classifier. It is
used to retrieve and classify results associated with that particular classifier in the database.
:param db: The `db` parameter refers to a Database connection object. This object is used to interact 
with the database where the classification results are stored. It allows performing operations such as
querying for results, inserting classification results, updating records, and checking for duplicates 
in the database.
:param helper: The `helper` parameter is an object that provides additional functionality to the classifier. 
It likely contains methods or attributes that assist in decoding data, handling specific operations, or 
performing other tasks that are necessary for the classification process.

Available data for the classifiers: 
url = data["url"] 
main = data["main"] 
position = data["position"] 
searchengine = data["searchengine"] 
searchengine_title = data["title"] 
searchengine_description = data["description"] 
ip = data["ip"] 
code = helper.decode_code(result["file_path"])
picture = helper.decode_picture(data["file_path"])
content_type = data["content_type"] 
error_code = data["error_code"] 
status_code = data["status_code"] 
final_url = data["final_url"] 
query = data["query"]

"""

import requests
import os
import inspect
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from datetime import datetime
from lxml import html
import json

# Import path setup from original script
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/libs/")
sys.path.append(currentdir + "/../")

# Import everything from the indicators module
from indicators import *
from seo_indicators import *

from classifier import *

class SeoScore(Classifier):
    """Handles SEO scoring logic"""
    def __init__(self, classifier_id: int = None, db=None, job_server: str = None):
        super().__init__(classifier_id, db, job_server)

        # Category weights (total = 100)
        self.category_weights = {
            'technical_seo': 35,
            'content_quality': 30,
            'user_experience': 20,
            'meta_elements': 15
        }

        self.classification_thresholds = {
            'most_probably_optimized': 75,
            'probably_optimized': 45,
            'probably_not_optimized': 20,
            'most_probably_not_optimized': 0
        }

        self.analytics_score_boost = 5

        # Tool weights for bonuses
        self.tool_weights = {
            'technical_seo': {
                'caching_tools': 10,
                'micro_tools': 5
            },
            'content_quality': {
                'content_tools': 10,
                'social_tools': 5
            },
            'user_experience': {
                'micro_tools': 5
            }
        }

    def process_result(self, result, indicators):
        """Process a single result and return indicators"""
        try:
            error_code = result["error_code"]
            status_code = result["status_code"]
            result_id = result["id"]

            if status_code != 200 or error_code:
                print(f"Skipping result with status code {status_code} or error code {error_code}")
                return None
            # Calculate score
            score_results = self.calculate_score(indicators)

            # Store category scores
            for category, score in score_results['category_scores'].items():
                self.insert_indicator(f"category_{category}", str(score), result_id)

            # Store analysis explanation
            self.insert_indicator('analysis_explanation', score_results['explanation'], result_id)

            # Store classification
            classification = self.get_classification(score_results['total_score'])
            self.insert_indicator('seo_classification', classification, result_id)

            return classification

        except Exception as e:
            print(f"Error processing result: {str(e)}")
            return None
        
    def get_indicators(self, result, helper):
            # Collect all indicators
            code = helper.decode_code(result["file_path"])
            soup = BeautifulSoup(code, 'lxml')
            main = result["main"]
            query = result["query"]
            url = result["url"]
            indicators = {}

            content_type = result["content_type"].lower()

            # Check if content type indicates HTML document
            is_html = (content_type == 'html' or 'html' in content_type)
            is_pdf = '.pdf' in url.lower() or '?pdf' in url.lower()

            if not is_html or is_pdf:
                indicators['is_html'] = False
                indicators['status'] = 'excluded'
                indicators['reason'] = f'Only HTML documents are included in SEO scoring. Found content type: {content_type}'
                indicators['exclusion_reason'] = f'Only HTML documents are included in SEO scoring. Found content type: {content_type}'
                indicators['content_type'] = content_type
                indicators['excluded'] = True

            #db.update_classification_result('excluded', result_id, classifier_id)
            #db.insert_indicator('exclusion_reason', indicators['reason'], classifier_id, result_id, job_server)
            #db.insert_indicator('content_type', indicators['content_type'], classifier_id, result_id, job_server)

            # Content Analysis
            indicators['content_length_score'] = analyze_content_length(soup)
            indicators['heading_structure_score'] = analyze_heading_structure(soup)

            # Link Analysis

            hyperlinks = identify_hyperlinks(get_hyperlinks(code, main), main)
            indicators['internal_links'] = hyperlinks["internal"]
            indicators['external_links'] = hyperlinks["external"]

            link_score = analyze_link_quality(hyperlinks["internal"], hyperlinks["external"])
            indicators['link_quality_score'] = link_score
            indicators['internal_link_count'] = hyperlinks["internal"]
            indicators['external_link_count'] = hyperlinks["external"]

            # Image Analysis
            indicators['image_optimization_score'] = analyze_images(soup)

            # Navigation Analysis
            indicators['navigation_score'] = analyze_navigation(soup)

            # Title Analysis
            title_score, title_text = analyze_title(soup)
            indicators['title_score'] = title_score
            indicators['title_text'] = title_text if title_text else ''

            # Description Analysis
            desc_score, desc_text = analyze_description(soup)
            indicators['description_score'] = desc_score
            indicators['description_text'] = desc_text if desc_text else ''

            # Social Tags Analysis
            social_score, social_tags = check_social_tags(soup)
            indicators['social_tags_score'] = social_score
            indicators['social_tags'] = social_tags

            # Keyword Analysis
            if query:
                keyword_score, keyword_reasons = analyze_keyword_usage(soup, url, query)
                indicators['keyword_optimization_score'] = keyword_score
                indicators['keyword_optimization_reasons'] = keyword_reasons

            # Original indicators from seo_rule_based.py
            plugins = identify_plugins(code)
            indicators.update({
                'tools_analytics': plugins['tools analytics'],
                'tools_seo': plugins['tools seo'],
                'tools_caching': plugins['tools caching'],
                'tools_social': plugins['tools social'],
                'tools_ads': plugins['tools ads']
            })

            # Technical indicators
            indicators['robots_txt'] = identify_robots_txt(main)
            indicators['loading_time'] = calculate_loading_time(url)

            # Parse URL and links
            parsed_url = urlparse(url)
            indicators['https'] = parsed_url.scheme == 'https'



            # Additional technical indicators
            indicators.update({
                'url_length': identify_url_length(url),
                'micros': identify_micros(code),
                'sitemap': identify_sitemap(code),
                'og': identify_og(code),
                'viewport': identify_viewport(code),
                'wordpress': identify_wordpress(code),
                'canonical': identify_canonical(code),
                'nofollow': identify_nofollow(code),
                'h1': identify_h1(code)
            })

            return indicators

    def get_classification(self, score):
        """Determine SEO optimization classification based on score"""
        if score >= self.classification_thresholds['most_probably_optimized']:
            return 'most_probably_optimized'
        elif score >= self.classification_thresholds['probably_optimized']:
            return 'probably_optimized'
        elif score >= self.classification_thresholds['probably_not_optimized']:
            return 'probably_not_optimized'
        else:
            return 'most_probably_not_optimized'

    def calculate_score(self, indicators):
        """Calculate overall SEO score based on indicators"""
        if not indicators:
            return {'total_score': 0}

        # Check if it's not an HTML document
        if not indicators.get('is_html', True):  # Default to True for backward compatibility
            return {
                'total_score': 0,
                'status': 'excluded',
                'reason': indicators.get('reason', 'Non-HTML document excluded from SEO scoring'),
                'content_type': indicators.get('content_type', 'unknown')
            }

        # If SEO plugins are detected, return perfect score
        if indicators.get('tools_seo', []):
            perfect_scores = {cat: 100 for cat in self.category_weights}
            self._last_category_scores = perfect_scores
            return {
                'total_score': 100,
                'category_scores': perfect_scores,
                'classification': 'most_probably_optimized',
                'explanation': self._generate_explanation(indicators)
            }

        # Calculate category scores
        category_scores = {}

        # Technical SEO (35%)
        technical_score = self._calculate_technical_score(indicators)

        # Content Quality (30%)
        content_score = self._calculate_content_score(indicators)

        # User Experience (20%)
        ux_score = self._calculate_user_experience_score(indicators)

        # Meta Elements (15%)
        meta_score = self._calculate_meta_score(indicators)

        category_scores = {
            'technical_seo': technical_score,
            'content_quality': content_score,
            'user_experience': ux_score,
            'meta_elements': meta_score
        }

        # Calculate weighted total
        total_score = sum(score * (self.category_weights[cat] / 100)
                        for cat, score in category_scores.items())

        # Add analytics boost if present
        if indicators.get('tools_analytics', []):
            total_score = min(100, total_score + self.analytics_score_boost)

        final_score = round(total_score, 2)

        # Store category scores for detailed explanation
        self._last_category_scores = category_scores

        return {
            'total_score': final_score,
            'category_scores': category_scores,
            'classification': self.get_classification(final_score),
            'explanation': self._generate_explanation(indicators)
        }

    def _calculate_technical_score(self, indicators):
        """Calculate technical SEO score"""
        score = 0

        # Core technical indicators
        if indicators.get('https', False):
            score += 20
        else:
            score -= 20
        if indicators.get('robots_txt', False):
            score += 20
        else:
            score -= 20
        if indicators.get('sitemap', False):
            score += 20
        if indicators.get('canonical', False):
            score += 20
        if 'application/ld+json' in str(indicators) or 'schema.org' in str(indicators):
            score += 20

        # Tool bonuses
        if indicators.get('tools_caching', []):
            score += self.tool_weights['technical_seo']['caching_tools']
        if indicators.get('tools_micro', []):
            score += self.tool_weights['technical_seo']['micro_tools']

        return min(100, max(0, score))

    def _calculate_content_score(self, indicators):
        """Calculate content quality score with meta element consideration"""
        score = 0

        # Content indicators (each weighted equally)
        score += indicators.get('content_length_score', 0) * 0.3
        score += indicators.get('heading_structure_score', 0) * 0.2
        score += indicators.get('link_quality_score', 0) * 0.2
        score += indicators.get('keyword_optimization_score', 0) * 0.3

        # Image optimization bonus
        score += indicators.get('image_optimization_score', 0) * 0.2

        # Penalize if basic meta elements are missing
        if indicators.get('title_score', 0) == 0 or indicators.get('description_score', 0) == 0:
            score = max(0, score - 20)  # Additional content penalty for missing basic meta

        # Tool bonuses
        if indicators.get('tools_content', []):
            score += self.tool_weights['content_quality']['content_tools']
        if indicators.get('tools_social', []):
            score += self.tool_weights['content_quality']['social_tools']

        return min(100, max(0, score))
    def _calculate_user_experience_score(self, indicators):
        """Calculate user experience score"""
        score = 0

        # Loading speed (40% of UX score)
        loading_time = indicators.get('loading_time', -1)
        if 0 < loading_time < 2:
            score += 40
        elif 2 <= loading_time < 3:
            score += 30
        elif 3 <= loading_time < 4:
            score += 20

        # Mobile friendliness (20% of UX score)
        if indicators.get('viewport', False):
            score += 20

        # Navigation (20% of UX score)
        score += (indicators.get('navigation_score', 0) * 0.2)

        # SSL security (20% of UX score)
        if indicators.get('https', False):
            score += 20

        # Tool bonus
        if indicators.get('tools_micro', []):
            score += self.tool_weights['user_experience']['micro_tools']

        return min(100, max(0, score))

    def _calculate_meta_score(self, indicators):
        """Calculate meta elements score with penalties for missing elements"""
        score = 0
        penalties = 0

        # Title tag (30%)
        title_score = indicators.get('title_score', 0)
        if title_score == 0:  # Missing title
            penalties += 30
        else:
            score += title_score * 0.3

        # Meta description (30%)
        desc_score = indicators.get('description_score', 0)
        if desc_score == 0:  # Missing description
            penalties += 30
        else:
            score += desc_score * 0.3

        # Social tags (40%)
        social_score = indicators.get('social_tags_score', 0)
        if social_score == 0:  # No social tags
            penalties += 20
        else:
            score += social_score * 0.4

        # Additional meta elements
        if not indicators.get('viewport', False):
            penalties += 10
        else:
            score += 10

        if not indicators.get('h1', False):
            penalties += 10
        else:
            score += 10

        # Apply penalties and ensure score doesn't go below 0
        final_score = max(0, score - penalties)
        return min(100, final_score)

    def _generate_explanation(self, indicators):
        """Generate detailed human-readable explanation of the score"""
        # Check if it's not HTML
        if not indicators.get('is_html', True):
            return indicators.get('reason', 'Non-HTML document excluded from SEO scoring')

        explanations = []

        # Tools and plugins detection
        if indicators.get('tools_analytics', []):
            explanations.append(f"Analytics tools detected (+{self.analytics_score_boost} points)")

        if indicators.get('tools_seo', []):
            explanations.append("SEO tools detected (major positive factor)")

        social_tools = indicators.get('tools_social', [])
        if social_tools:
            explanations.append(f"Social media tools detected: {len(social_tools)} (+{min(len(social_tools) * 2, 3)} points)")

        # Technical details
        loading_time = indicators.get('loading_time', -1)
        if loading_time > 0:
            explanations.append(f"Page loading time: {loading_time:.1f}s")

        # Category score breakdowns
        if hasattr(self, '_last_category_scores'):
            explanations.append("\nScore breakdown by category:")

            # Technical SEO
            tech_score = self._last_category_scores['technical_seo']
            tech_weight = self.category_weights['technical_seo']
            tech_contribution = round(tech_score * (tech_weight / 100), 2)
            explanations.append(f"- Technical SEO: {tech_score:.1f}/100 (weight: {tech_weight}%, contributes {tech_contribution} points)")

            # Content Quality
            content_score = self._last_category_scores['content_quality']
            content_weight = self.category_weights['content_quality']
            content_contribution = round(content_score * (content_weight / 100), 2)
            explanations.append(f"- Content Quality: {content_score:.1f}/100 (weight: {content_weight}%, contributes {content_contribution} points)")

            # User Experience
            ux_score = self._last_category_scores['user_experience']
            ux_weight = self.category_weights['user_experience']
            ux_contribution = round(ux_score * (ux_weight / 100), 2)
            explanations.append(f"- User Experience: {ux_score:.1f}/100 (weight: {ux_weight}%, contributes {ux_contribution} points)")

            # Meta Elements
            meta_score = self._last_category_scores['meta_elements']
            meta_weight = self.category_weights['meta_elements']
            meta_contribution = round(meta_score * (meta_weight / 100), 2)
            explanations.append(f"- Meta Elements: {meta_score:.1f}/100 (weight: {meta_weight}%, contributes {meta_contribution} points)")

            # Calculate total
            total_base = sum([tech_contribution, content_contribution, ux_contribution, meta_contribution])
            explanations.append(f"\nBase score: {total_base:.2f}")

            # Analytics boost explanation if applicable
            if indicators.get('tools_analytics', []):
                explanations.append(f"Analytics boost: +{self.analytics_score_boost}")
                explanations.append(f"Final score: {min(100, total_base + self.analytics_score_boost):.2f}")

        return ". ".join(explanations)

if __name__ == "__main__":
    pass