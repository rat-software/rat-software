"""
The `main` function orchestrates the classification process for a classifier by checking for
duplicates, classifying results, and updating the database with classification information.
"""

import requests
import os
import inspect
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from datetime import datetime
import json

# Import path setup from original script
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/libs/")
sys.path.append(currentdir + "/../")

# Indicators import (now handles spacy internally)
from geo_indicators import *
from classifier import *

class GeoScore(Classifier):
    """Handles Generative Engine Optimization (GEO) scoring logic"""
    
    def __init__(self, classifier_id: int = None, db=None, job_server: str = None):
        super().__init__(classifier_id, db, job_server)
        
        self.category_weights = {
            'structure_formatting': 20,    
            'authority_trust': 40,         
            'semantics_readability': 30,   
            'technical_baseline': 10       
        }

        self.classification_thresholds = {
            'highly_geo_optimized': 75,
            'probably_geo_optimized': 45,
            'probably_not_geo_optimized': 20,
            'poorly_geo_optimized': 0
        }

    def get_indicators(self, result, helper):
        """
        Extract indicators from a single result, ensuring all keys are always populated.
        """
        url = result.get("url") or ""
        main = result.get("main") or ""
        file_path = result.get("file_path")
        code = helper.decode_code(file_path) if file_path else ""
        error_code = result.get("error_code")
        status_code = result.get("status_code", 200)
        query = result.get("query", "")
        content_type = str(result.get("content_type") or "text/html").lower()

        indicators = {}

        is_html = (content_type == 'html' or 'html' in content_type)
        is_pdf = '.pdf' in url.lower() or '?pdf' in url.lower()

        exclusion_reason = None
        if not is_html or is_pdf:
            exclusion_reason = f'Content type {content_type} excluded from GEO scoring'
            code = ""
        elif status_code != 200 or error_code:
            exclusion_reason = f'Skipped due to status code {status_code} or error {error_code}'
            code = ""

        if exclusion_reason:
            indicators['exclusion_reason_notice'] = exclusion_reason
            indicators['is_html'] = False
        else:
            indicators['is_html'] = True

        soup = BeautifulSoup(code, 'lxml') if code else BeautifulSoup("", 'lxml')

        # --- DYNAMIC LANGUAGE & NLP MODEL LOADING ---
        lang_attr = soup.find('html').get('lang') if soup.find('html') else None
        clean_text = soup.get_text(separator=' ', strip=True) if code else ""
        lang_code = detect_language(clean_text, lang_attr)
        nlp = get_spacy_model(lang_code)

        if code:
            length_score, word_cnt, char_cnt = self.analyze_content_length(soup)
            indicators['content_length_score'] = length_score
            indicators['word_count'] = word_cnt
            indicators['character_count'] = char_cnt
        else:
            indicators['content_length_score'] = 0
            indicators['word_count'] = 0
            indicators['character_count'] = 0
            
        indicators['heading_structure_score'] = self.analyze_heading_structure(soup) if code else 0

        # --- SEMANTIC VECTOR OVERLAP ---
        fk_column = result.get("fk_column", "result")
        if fk_column == 'result_ai_source' and code:
            segment_text = self.db.get_ai_segment_text_for_source(result['id']) 
            
            indicators['ai_overview_word_count'] = len(segment_text.split()) if segment_text else 0
            
            sibling_sources = self.db.get_sibling_sources_for_segment(result['id'])
            sources_dict = {result['id']: code}
            
            for sibling in sibling_sources:
                sibling_path = sibling.get('file_path')
                sibling_code = helper.decode_code(sibling_path) if sibling_path else ""
                sources_dict[sibling['id']] = sibling_code
                
            overlap_metrics = analyze_multi_source_overlap_semantic(segment_text, sources_dict)
            if result['id'] in overlap_metrics:
                indicators['ai_semantic_similarity_percentage'] = overlap_metrics[result['id']]['semantic_similarity_percentage']
        else:
            na_text = "N/A - Organic search result (no AI segment)"
            indicators['ai_semantic_similarity_percentage'] = na_text
            indicators['ai_overview_word_count'] = na_text

        # Link analysis (Now includes high-trust links)
        if main and code:
            hyperlinks = identify_hyperlinks(get_hyperlinks(code, main), main)
            indicators['internal_links'] = hyperlinks["internal"]
            indicators['external_links'] = hyperlinks["external"]
            indicators['high_trust_links'] = hyperlinks["high_trust_links"]
            indicators['link_quality_score'] = self.analyze_link_quality(
                hyperlinks["internal"], 
                hyperlinks["external"], 
                hyperlinks["high_trust_links"]
            )
            indicators['robots_txt'] = identify_robots_txt(main)
        else:
            indicators['internal_links'] = 0
            indicators['external_links'] = 0
            indicators['high_trust_links'] = 0
            indicators['link_quality_score'] = 0
            indicators['robots_txt'] = 0

        indicators['title_score'], indicators['title_text'] = self.analyze_title(soup, nlp) if code else (0, None)
        indicators['description_score'], indicators['description_text'] = self.analyze_description(soup, nlp) if code else (0, None)
        
        if query and code:
            indicators['keyword_optimization_score'], indicators['keyword_optimization_reasons'] = self.analyze_keyword_usage(soup, url, query, nlp)
            
            # PASSED THE NLP MODEL HERE:
            indicators['keyword_density'] = identify_keyword_density(code, query, nlp)
            
            indicators['keywords_in_code'] = identify_keywords_in_source(code, query, nlp)
            indicators['keywords_in_url'] = identify_keywords_in_url(url, query, nlp)
        else:
            indicators['keyword_optimization_score'], indicators['keyword_optimization_reasons'] = (0, [])
            indicators['keyword_density'] = 0.0
            indicators['keywords_in_code'] = 0
            indicators['keywords_in_url'] = 0
            
        if url.startswith('ai://'):
            indicators['loading_time'] = -1
            indicators['https'] = True
        else:
            indicators['loading_time'] = calculate_loading_time(url) if code else 999.0
            indicators['https'] = urlparse(url).scheme == 'https'
        
        indicators.update({
            'url_length': identify_url_length(url),
            'micros': identify_micros(code) if code else [],
            'sitemap': identify_sitemap(code) if code else 0,
            'viewport': identify_viewport(code) if code else 0,
            'canonical': identify_canonical(code) if code else 0,
            'nofollow': identify_nofollow(code) if code else 0,
            'h1': identify_h1(code) if code else 0,
            'h2': identify_h2(code) if code else 0,
            'microdata_advanced_score': analyze_microdata_advanced(code) if code else 0,
            'company_signals': analyze_company_signals(code) if code else 0,
            'readability_score': analyze_readability(code, lang_code) if code else 0.0
        })

        if code:
            indicators.update(identify_structure_elements(code))
            indicators.update(identify_faqs_advanced(code))
            indicators.update(analyze_paragraphs(code))
            indicators.update(identify_authority_signals(code))
            indicators.update(identify_statistics_and_entities_universal(code, nlp))
        else:
            indicators.update({
                'tables': 0, 'ul_lists': 0, 'ol_lists': 0, 'list_items': 0,
                'schema_faq_present': 0, 'schema_qa_count': 0, 'semantic_qa_count': 0, 'faq_css_classes': 0,
                'p_count': 0, 'avg_words_per_p': 0, 'avg_sentences_per_p': 0,
                'blockquotes': 0, 'author_tags': 0, 'percentage_count': 0, 'year_count': 0, 'organizations_count': 0
            })

        return indicators

    def process_result(self, result, indicators):
        try:
            result_id = result["id"]
            score_results = self.calculate_score(indicators)

            if 'category_scores' in score_results:
                for category, score in score_results['category_scores'].items():
                    self.insert_indicator(f"category_{category}", str(score), result_id)

            if 'explanation' in score_results:
                self.insert_indicator('geo_explanation', score_results['explanation'], result_id)
                
            if 'classification' in score_results:
                self.insert_indicator('geo_classification', score_results['classification'], result_id)

            return score_results['total_score']
        except Exception as e:
            print(f"Error processing result: {str(e)}")
            return 'error'

    def get_classification(self, score):
        if score >= self.classification_thresholds['highly_geo_optimized']:
            return 'highly_geo_optimized'
        elif score >= self.classification_thresholds['probably_geo_optimized']:
            return 'probably_geo_optimized'
        elif score >= self.classification_thresholds['probably_not_geo_optimized']:
            return 'probably_not_geo_optimized'
        else:
            return 'poorly_geo_optimized'

    def calculate_score(self, indicators):
        if not indicators:
            return {'total_score': 0}

        structure_score = self._calculate_structure_score(indicators)
        authority_score = self._calculate_authority_score(indicators)
        semantics_score = self._calculate_semantics_score(indicators)
        technical_score = self._calculate_technical_score(indicators)

        category_scores = {
            'structure_formatting': structure_score,
            'authority_trust': authority_score,
            'semantics_readability': semantics_score,
            'technical_baseline': technical_score
        }

        total_score = sum(score * (self.category_weights[cat] / 100)
                        for cat, score in category_scores.items())

        final_score = round(total_score, 2)
        self._last_category_scores = category_scores
        explanation = self._generate_explanation(indicators)
        classification = self.get_classification(final_score)

        gatekeeper_failed = False
        gatekeeper_reason = ""
        
        if 'exclusion_reason_notice' in indicators:
            gatekeeper_failed = True
            gatekeeper_reason = indicators['exclusion_reason_notice']
            
        elif indicators.get('robots_txt', 0) == 1:
            gatekeeper_failed = False 
            explanation = f"Notice: Restrictive robots.txt (AI scraper blocks) found, but ignored for scoring. | {explanation}"
            
        else:
            loading_time = indicators.get('loading_time', 0)
            if loading_time > 10.0:
                gatekeeper_failed = True
                gatekeeper_reason = f"Gatekeeper failed: Page loading time is critically high ({round(loading_time, 2)}s)."

        if gatekeeper_failed:
            final_score = 0
            classification = 'poorly_geo_optimized'
            explanation = f"Notice: {gatekeeper_reason} | {explanation}"

        return {
            'total_score': final_score,
            'category_scores': category_scores,
            'classification': classification,
            'explanation': explanation
        }

    def _calculate_semantics_score(self, indicators):
        score = 0
        avg_words = indicators.get('avg_words_per_p', 0)
        
        # 1. Paragraph Architecture
        if 30 <= avg_words <= 70:
            score += 40
        elif 15 <= avg_words <= 90:
            score += 20
        else:
            score += 5
            
        # 2. Readability
        readability = indicators.get('readability_score', 50)
        if 60 <= readability <= 75:
            score += 40
        elif 40 <= readability <= 90:
            score += 25
        elif 0 <= readability < 40 or readability > 90:
            score += 15 # Academic/Complex text still gets partial credit
        else:
            score += 0 

        # 3. Q&A / Conversational Formatting
        # Generative Engines prioritize Q&A conversational formats heavily.
        qa_signals = indicators.get('schema_faq_present', 0) + indicators.get('semantic_qa_count', 0)
        if qa_signals > 0:
            score += 20
            
        # 4. Keyword Stuffing Penalty
        kw_density = indicators.get('keyword_density', 0)
        if kw_density > 3.0: 
            score -= 20
            
        return max(0, min(100, score))

    def _calculate_structure_score(self, indicators):
        score = 0
        score += indicators.get('heading_structure_score', 0) * 0.3
        score += indicators.get('content_length_score', 0) * 0.3
        score += indicators.get('title_score', 0) * 0.1
        score += indicators.get('description_score', 0) * 0.1
        
        if indicators.get('tables', 0) > 0:
            score += 10
        if indicators.get('ul_lists', 0) > 0 or indicators.get('ol_lists', 0) > 0:
            score += 10
            
        return max(0, min(100, score))

    def _calculate_authority_score(self, indicators):
        score = 0
        score += indicators.get('link_quality_score', 0) * 0.4
        
        # Replaced N-grams with Vector similarity score
        semantic_sim = indicators.get('ai_semantic_similarity_percentage', 0.0)
        
        if isinstance(semantic_sim, str):
            semantic_sim = 0.0
            
        if semantic_sim >= 70:
            score += 25
        elif semantic_sim >= 40:
            score += 15
        elif semantic_sim >= 15:
            score += 5
            
        if indicators.get('company_signals', 0) > 0:
            score += 10
        if indicators.get('author_tags', 0) > 0:
            score += 5
            
        if indicators.get('percentage_count', 0) > 0:
            score += 5
        if indicators.get('year_count', 0) > 0:
            score += 5
        if indicators.get('organizations_count', 0) > 0:
            score += 10
            
        return max(0, min(100, score))

    def _calculate_technical_score(self, indicators):
        score = 0
        if indicators.get('https', False):
            score += 30
            
        loading_time = indicators.get('loading_time', -1)
        if 0 < loading_time < 2:
            score += 40
        elif 2 <= loading_time < 3:
            score += 20
            
        if indicators.get('micros', []) or indicators.get('microdata_advanced_score', 0) > 0:
            score += 30
            
        return min(100, score)

    def _generate_explanation(self, indicators):
        if not indicators.get('is_html', True):
            return indicators.get('reason', 'Non-HTML document excluded from scoring')

        explanations = []
        if hasattr(self, '_last_category_scores'):
            explanations.append("GEO Score breakdown by category:")

            struct_score = self._last_category_scores['structure_formatting']
            struct_weight = self.category_weights['structure_formatting']
            struct_contrib = round(struct_score * (struct_weight / 100), 2)
            explanations.append(f"- Structure & Formatting: {struct_score:.1f}/100 (weight: {struct_weight}%, contributes {struct_contrib} points)")

            auth_score = self._last_category_scores['authority_trust']
            auth_weight = self.category_weights['authority_trust']
            auth_contrib = round(auth_score * (auth_weight / 100), 2)
            explanations.append(f"- Authority & Trust: {auth_score:.1f}/100 (weight: {auth_weight}%, contributes {auth_contrib} points)")

            sem_score = self._last_category_scores['semantics_readability']
            sem_weight = self.category_weights['semantics_readability']
            sem_contrib = round(sem_score * (sem_weight / 100), 2)
            explanations.append(f"- Semantics & Readability: {sem_score:.1f}/100 (weight: {sem_weight}%, contributes {sem_contrib} points)")

            tech_score = self._last_category_scores['technical_baseline']
            tech_weight = self.category_weights['technical_baseline']
            tech_contrib = round(tech_score * (tech_weight / 100), 2)
            explanations.append(f"- Technical Baseline: {tech_score:.1f}/100 (weight: {tech_weight}%, contributes {tech_contrib} points)")

            total_base = sum([struct_contrib, auth_contrib, sem_contrib, tech_contrib])
            explanations.append(f"\nFinal GEO Score: {total_base:.2f}")
            
            kw_density = indicators.get('keyword_density', 0)
            if kw_density > 3.0:
                explanations.append(f"\nWARNING: High keyword density ({kw_density}%) detected! Semantics score was penalized for over-optimization.")

        return ". ".join(explanations)

    def analyze_content_length(self, soup):
        # We re-parse from string so we don't destroy the original soup object
        clean_soup = BeautifulSoup(str(soup), 'lxml')
        
        # Remove code, headers, and footers
        for tag in clean_soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
            
        text = clean_soup.get_text(separator=' ', strip=True)
        words = len(text.split())
        chars = len(text)

        # Scoring remains the same
        if words >= 1500: score = 100
        elif words >= 1000: score = 80
        elif words >= 500: score = 60
        elif words >= 300: score = 40
        else: score = max(0, (words / 300) * 40)
        
        return score, words, chars

    def analyze_heading_structure(self, soup):
        score = 0
        if len(soup.find_all('h1')) == 1: score += 40
        if soup.find_all(['h2', 'h3']): score += 30
        if soup.find_all(['h4', 'h5', 'h6']): score += 30
        return score

    def analyze_link_quality(self, internal_links, external_links, high_trust_links=0):
        score = 0
        total_links = internal_links + external_links
        
        if total_links > 0:
            ratio = internal_links / total_links
            if 0.6 <= ratio <= 0.8:
                score += 30
            elif 0.4 <= ratio <= 0.9:
                score += 20
                
        if total_links >= 10:
            score += 30
        elif total_links >= 5:
            score += 15
            
        if high_trust_links >= 3:
            score += 40
        elif high_trust_links > 0:
            score += 20
            
        return min(100, score)

    def analyze_title(self, soup, nlp_model=None):
        title = soup.find('title')
        if not title: return 0, None
        title_text = title.text.strip()
        if not title_text: return 0, None
            
        score = 0
        if title_text.lower() in ['untitled', 'home', 'page', 'startseite']:
            return 0, title_text
            
        if len(title_text) >= 15: score += 40
        else: score += 20
            
        if nlp_model:
            doc = nlp_model(title_text)
            if len(doc.ents) > 0: score += 60
                
        return min(100, score), title_text

    def analyze_description(self, soup, nlp_model=None):
        desc = soup.find('meta', {'name': 'description'})
        if not desc: return 0, None
        content = desc.get('content', '')
        if not content.strip(): return 0, None
            
        score = 0
        if content.lower() in ['description', 'website description', 'meta description']:
            return 0, content
            
        if len(content) >= 40: score += 40
        else: score += 20
            
        if nlp_model:
            doc = nlp_model(content)
            if len(doc.ents) >= 2: score += 60
            elif len(doc.ents) == 1: score += 30
                
        return min(100, score), content

    def analyze_keyword_usage(self, soup, url, query, nlp_model=None):
        if not query:
            return self.analyze_general_content_optimization(soup, nlp_model)
        return self.analyze_specific_keyword(soup, url, query)

    def analyze_general_content_optimization(self, soup, nlp_model=None):
        score, reasons = 0, []
        title = soup.find('title')
        if title and len(title.text.strip()) > 10:
            score += 15
            reasons.append('Meaningful title present')
            
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content') and len(meta_desc.get('content').strip()) > 30:
            score += 15
            reasons.append('Meaningful description present')
                
        headings = soup.find_all(['h1', 'h2', 'h3'])
        if headings:
            if len(soup.find_all('h1')) == 1:
                score += 20
                reasons.append('Proper H1 usage')
            if len(headings) >= 3:
                score += 20
                reasons.append('Good heading structure')
                
            if nlp_model:
                headings_text = " ".join([h.text for h in headings])
                doc = nlp_model(headings_text)
                if len(doc.ents) > 3:
                    score += 30
                    reasons.append('High entity density in structural headings')
                
        return min(100, score), reasons

    def analyze_specific_keyword(self, soup, url, query):
        score, reasons = 0, []
        query = query.lower()
        if query in url.lower():
            score += 25
            reasons.append('Keyword in URL')
        title = soup.find('title')
        if title and query in title.text.lower():
            score += 25
            reasons.append('Keyword in title')
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and query in meta_desc.get('content', '').lower():
            score += 25
            reasons.append('Keyword in description')
        headers = soup.find_all(['h1', 'h2', 'h3'])
        if any(query in h.text.lower() for h in headers):
            score += 25
            reasons.append('Keyword in headers')
        return score, reasons


if __name__ == "__main__":
    pass