import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from seleniumbase import Driver
import time
import re
import fnmatch
import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from lxml import html
import pandas as pd
from datetime import datetime
import inspect
import sys

from urllib.parse import urlsplit, urlparse

# Define the path for configurations and extensions
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
ext_path = os.path.join(currentdir, "extension")

# Import path setup from original script
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/libs/")

# Import everything from the indicators module
from indicators import *

class SEOScorer:
    """Handles SEO scoring logic"""
    def __init__(self):
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

        # If SEO plugins are detected, return perfect score
        if indicators.get('tools_seo', []):
            return {
                'total_score': 100,
                'category_scores': {cat: 100 for cat in self.category_weights},
                'classification': 'most_probably_optimized',
                'explanation': "SEO plugins detected - Strong indication of professional optimization"
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
        """Generate human-readable explanation of the score"""
        explanations = []

        if indicators.get('tools_analytics', []):
            explanations.append(f"Analytics tools detected (+{self.analytics_score_boost} points)")

        if indicators.get('tools_seo', []):
            explanations.append("SEO tools detected (major positive factor)")

        social_tools = indicators.get('tools_social', [])
        if social_tools:
            explanations.append(f"Social media tools detected: {len(social_tools)} (+{min(len(social_tools) * 2, 3)} points)")

        loading_time = indicators.get('loading_time', -1)
        if loading_time > 0:
            explanations.append(f"Page loading time: {loading_time:.1f}s")

        return ". ".join(explanations)

class SEOAnalyzer:
    def __init__(self):
        self.scorer = SEOScorer()

    def setup_selenium(self):
        return Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=True,
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            locale_code="de",
            extension_dir=ext_path,
            no_sandbox=True
        )

    def get_source_code(self, url):
        """Fetch webpage source code using Selenium"""
        driver = self.setup_selenium()

        def simulate_scrolling(driver, required_height):
            """
            Scrolls the webpage to the specified height.

            Args:
                driver (webdriver): The Selenium WebDriver instance.
                required_height (int): The height to scroll to.

            Returns:
                list: The driver and the required height after scrolling.
            """
            height = required_height
            current_height = 0
            block_size = 500
            scroll_time_in_seconds = 1
            scrolling = []
            max_height = 20000

            while current_height < height and current_height < max_height:
                #print(current_height)
                current_height += block_size
                scroll_to = f"window.scrollTo(0,{current_height})"
                driver.execute_script(scroll_to)
                height = driver.execute_script('return document.body.parentNode.scrollHeight')
                time.sleep(scroll_time_in_seconds)

            driver.execute_script("window.scrollTo(0,1)")
            required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
            scrolling = [driver, required_height]
            return scrolling

        try:
            driver.set_page_load_timeout(30)
            driver.get(url)
            time.sleep(2)  # Allow for dynamic content
            required_height = 2000
            scrolling = simulate_scrolling(driver, required_height)
            driver = scrolling[0]

            return driver.page_source
        finally:
            if driver:
                driver.quit()

    def analyze_content_length(self, soup):
        """Analyze content length and return score"""
        text = soup.get_text()
        words = len(text.split())

        if words >= 1500:
            return 100
        elif words >= 1000:
            return 80
        elif words >= 500:
            return 60
        elif words >= 300:
            return 40
        else:
            return max(0, (words / 300) * 40)

    def analyze_heading_structure(self, soup):
        """Analyze heading structure and return score"""
        score = 0
        if len(soup.find_all('h1')) == 1:
            score += 40
        if soup.find_all(['h2', 'h3']):
            score += 30
        if soup.find_all(['h4', 'h5', 'h6']):
            score += 30
        return score

    def analyze_link_quality(self, soup):
        """Analyze link quality and structure"""
        links = soup.find_all('a')
        if not links:
            return 0, 0, 0

        score = 0
        internal_links = 0
        external_links = 0
        total_links = len(links)

        for link in links:
            href = link.get('href', '')
            if href.startswith(('http', 'https')):
                external_links += 1
            elif href and not href.startswith(('#', 'javascript:')):
                internal_links += 1

        # Score based on internal/external link ratio
        if internal_links + external_links > 0:
            ratio = internal_links / (internal_links + external_links)
            if 0.6 <= ratio <= 0.8:
                score += 50
            elif 0.4 <= ratio <= 0.9:
                score += 30

        # Score based on total number of links
        if total_links >= 10:
            score += 50
        elif total_links >= 5:
            score += 25

        return score, internal_links, external_links

    def analyze_images(self, soup):
        """Calculate percentage of images with alt text"""
        images = soup.find_all('img')
        if not images:
            return 0
        images_with_alt = len([img for img in images if img.get('alt')])
        return round((images_with_alt / len(images)) * 100)

    def analyze_navigation(self, soup):
        """Analyze navigation structure"""
        score = 0
        if soup.find(['nav', 'menu']):
            score += 40
        if soup.find('footer'):
            score += 30
        if soup.find('form'):
            score += 30
        return score

    def analyze_title(self, soup):
        """Analyze title tag with stricter scoring"""
        title = soup.find('title')
        if not title:
            return 0, None

        title_text = title.text.strip()
        if not title_text:  # Empty title tag
            return 0, None

        length = len(title_text)
        score = 0

        if 50 <= length <= 60:
            score = 100
        elif 40 <= length <= 70:
            score = 80
        elif 30 <= length <= 80:
            score = 60
        else:
            score = 40

        # Additional check for common SEO issues
        if title_text.lower() in ['untitled', 'home', 'page']:
            score = max(0, score - 30)  # Penalty for generic titles

        return score, title_text

    def analyze_description(self, soup):
        """Analyze meta description with stricter scoring"""
        desc = soup.find('meta', {'name': 'description'})
        if not desc:
            return 0, None

        content = desc.get('content', '')
        if not content.strip():  # Empty description
            return 0, None

        length = len(content)
        score = 0

        if 150 <= length <= 160:
            score = 100
        elif 130 <= length <= 170:
            score = 80
        elif 110 <= length <= 190:
            score = 60
        else:
            score = 40

        # Additional check for common SEO issues
        if content.lower() in ['description', 'website description']:
            score = max(0, score - 30)  # Penalty for generic descriptions

        return score, content

    def check_social_tags(self, soup):
        """Check for social media meta tags"""
        score = 0
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})

        if og_tags:
            score += 50
        if twitter_tags:
            score += 50

        return score, {
            'og_tags': [tag.get('property', '') for tag in og_tags],
            'twitter_tags': [tag.get('name', '') for tag in twitter_tags]
        }

    def analyze_keyword_usage(self, soup, url, query):
        """Analyze keyword usage in content"""
        print(query)
        if not query:
            return self.analyze_general_content_optimization(soup)
        return self.analyze_specific_keyword(soup, url, query)

    def analyze_general_content_optimization(self, soup):
        """Analyze general content optimization without specific keyword"""
        score = 0
        reasons = []

        # Check title optimization
        title = soup.find('title')
        if title and 20 <= len(title.text.strip()) <= 70:
            score += 25
            reasons.append('Optimized title length')

        # Check meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content = meta_desc.get('content')
            if 120 <= len(content) <= 160:
                score += 25
                reasons.append('Optimized description length')

        # Check heading structure
        headings = soup.find_all(['h1', 'h2', 'h3'])
        if headings:
            if len(soup.find_all('h1')) == 1:
                score += 25
                reasons.append('Proper H1 usage')
            if len(headings) >= 3:
                score += 25
                reasons.append('Good heading structure')

        return score, reasons

    def analyze_specific_keyword(self, soup, url, query):
        """Analyze keyword-specific optimization"""
        score = 0
        reasons = []
        query = query.lower()

        # URL contains keyword
        if query in url.lower():
            score += 25
            reasons.append('Keyword in URL')

        # Title contains keyword
        title = soup.find('title')
        if title and query in title.text.lower():
            score += 25
            reasons.append('Keyword in title')

        # Meta description contains keyword
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and query in meta_desc.get('content', '').lower():
            score += 25
            reasons.append('Keyword in description')

        # Headers contain keyword
        headers = soup.find_all(['h1', 'h2', 'h3'])
        if any(query in h.text.lower() for h in headers):
            score += 25
            reasons.append('Keyword in headers')

        return score, reasons

    def process_url(self, url, query=""):


        def check_url_protocol(url):
            """Check if URL is accessible with HTTPS or HTTP and return working URL"""
            # Clean the URL first
            url = url.strip().lower()
            # Remove any existing protocol

            try:
                if url.startswith('http://'):
                    url = url[7:]
                elif url.startswith('https://'):
                    url = url[8:]
            except:
                pass

            # Try HTTPS first, then HTTP
            for protocol in ['https://', 'http://']:
                try:
                    test_url = f"{protocol}{url}"
                    response = requests.head(test_url, timeout=5, allow_redirects=True)
                    if response.status_code < 400:
                        return test_url
                except:
                    return f"https://{url}"

              
                

        url = check_url_protocol(url)
        print(query)
        """Process a single URL and return its indicators and score"""
        try:

            # Fetch the page content
            code = self.get_source_code(url)
            if not code:
                return None

            # Parse content
            soup = BeautifulSoup(code, 'lxml')

            # Collect indicators
            indicators = {}

            # Content Analysis
            indicators['content_length_score'] = self.analyze_content_length(soup)
            indicators['heading_structure_score'] = self.analyze_heading_structure(soup)

            # Link Analysis
            link_score, internal_count, external_count = self.analyze_link_quality(soup)
            indicators['link_quality_score'] = link_score
            indicators['internal_link_count'] = internal_count
            indicators['external_link_count'] = external_count

            # Image Analysis
            indicators['image_optimization_score'] = self.analyze_images(soup)

            # Navigation Analysis
            indicators['navigation_score'] = self.analyze_navigation(soup)

            # Title Analysis
            title_score, title_text = self.analyze_title(soup)
            indicators['title_score'] = title_score
            indicators['title_text'] = title_text if title_text else ''

            # Description Analysis
            desc_score, desc_text = self.analyze_description(soup)
            indicators['description_score'] = desc_score
            indicators['description_text'] = desc_text if desc_text else ''

            # Social Tags Analysis
            social_score, social_tags = self.check_social_tags(soup)
            indicators['social_tags_score'] = social_score
            indicators['social_tags'] = social_tags


            # Keyword Analysis (use general optimization if no query provided)
            if query and query.strip():
                keyword_score, keyword_reasons = self.analyze_keyword_usage(soup, url, query)
            else:
                keyword_score, keyword_reasons = self.analyze_general_content_optimization(soup)
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

            try:
                parsed_uri = urlparse(url)
                main = f'{parsed_uri.scheme}://{parsed_uri.netloc}/'
            except Exception:
                main = url

            # Technical indicators
            indicators['robots_txt'] = identify_robots_txt(main)
            indicators['loading_time'] = calculate_loading_time(url)


            # Technical indicators
            indicators['https'] = urlparse(url).scheme == 'https'


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

            # Calculate final score
            score_results = self.scorer.calculate_score(indicators)

            print("\n=== Score Results ===")
            for key, value in score_results.items():
                print(f"{key}: {value}")

            return {
                'url': url,
                'query': query,
                'indicators': indicators,
                'score_results': score_results
            }

        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None

    def process_csv(self, input_csv, output_csv, max_workers=5):
        """Process URLs from CSV and write results incrementally to output CSV"""
        # Read input CSV and handle missing query column
        df = pd.read_csv(input_csv)

        if 'query' not in df.columns:
            df['query'] = ''  # Add empty query column if not present

        # Create output CSV with headers
        first_result = None
        header_written = False

        def process_and_write_result(row):
            """Process a single URL and write its result to the CSV"""
            nonlocal header_written, first_result

            try:
                result = self.process_url(row['url'], row['query'])
                if not result:
                    return None

                # Prepare row data
                row_data = {
                    'url': result['url'],
                    'query': result['query'],
                    'total_score': result['score_results']['total_score'],
                    'classification': result['score_results']['classification']
                }

                # Add all indicators
                for key, value in result['indicators'].items():
                    if isinstance(value, (dict, list)):
                        row_data[key] = json.dumps(value)
                    else:
                        row_data[key] = value

                # Add category scores
                for category, score in result['score_results']['category_scores'].items():
                    row_data[f'{category}_score'] = score

                # Convert to DataFrame
                df_row = pd.DataFrame([row_data])

                # Write to CSV
                mode = 'a' if header_written else 'w'
                header = not header_written
                df_row.to_csv(output_csv, mode=mode, header=header, index=False)

                if not header_written:
                    header_written = True

                print(f"Processed and wrote results for {row['url']}")
                return result

            except Exception as e:
                print(f"Error processing {row['url']}: {str(e)}")
                return None

        # Process URLs in parallel with immediate writing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for _, row in df.iterrows():
                future = executor.submit(process_and_write_result, row)
                futures.append(future)

            # Wait for all futures to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in thread: {str(e)}")

        print(f"All results have been written to {output_csv}")

def main():
    """Main function to run the SEO analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description='SEO Analysis Tool')
    parser.add_argument('input_csv', help='Input CSV file with URLs and queries')
    parser.add_argument('output_csv', help='Output CSV file for results')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers')

    args = parser.parse_args()

    analyzer = SEOAnalyzer()
    analyzer.process_csv(args.input_csv, args.output_csv, args.workers)

if __name__ == "__main__":
    main()
