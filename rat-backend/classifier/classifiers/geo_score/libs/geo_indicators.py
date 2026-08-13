import fnmatch
from urllib.parse import urlparse
import csv
import json
import time
import os
import inspect
from seleniumbase import Driver
from bs4 import BeautifulSoup
from lxml import html
import re
import spacy
from spacy.cli import download as spacy_download
import textstat
from langdetect import detect
from collections import defaultdict
import requests


#pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

os.environ["CUDA_VISIBLE_DEVICES"] = ""  
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import warnings
import logging
# 1. Blindfold PyTorch (Force CPU & Hide NVIDIA drivers)
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# 2. Muzzle Hugging Face and Transformers Environment Variables
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# 3. Catch ALL Python warnings (Not just UserWarnings)
warnings.filterwarnings("ignore")

# 4. Force silence on all Hugging Face and AI-related loggers
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# --- SEMANTIC VECTOR SIMILARITY ---
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    # Loads a very fast, lightweight embedding model
    EMBEDDING_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
except ImportError:
    print("Warning: sentence_transformers or scikit-learn not found. Semantic overlap will fallback to 0. Run: pip install sentence-transformers scikit-learn")
    EMBEDDING_MODEL = None

# --- DYNAMIC NLP MODELS ---
SPACY_MODELS = {}

def detect_language(text, html_lang_attr=None):
    """
    Dynamically detects the language of the text without restricting to a hardcoded list.
    Returns the ISO 639-1 code (e.g., 'en', 'de', 'it', 'zh').
    """
    # 1. Try HTML lang attribute first (Fastest)
    if html_lang_attr:
        ext = html_lang_attr.split('-')[0].lower()
        if len(ext) == 2 or len(ext) == 3:  # Basic validation of ISO code
            return ext
            
    # 2. Content-based detection using langdetect
    if len(text) > 20:
        try:
            return detect(text)
        except:
            pass
            
    # 3. Ultimate Fallback
    return 'en'

def get_spacy_model(lang_code):
    """
    Flexibly maps any detected language to its corresponding spaCy model.
    Auto-downloads it if missing. Falls back to multilingual if no specific model exists.
    """
    # Comprehensive map of official spaCy small models. 
    # (Note: spaCy naming isn't perfectly uniform, so mapping is the safest approach)
    spacy_model_map = {
        'en': 'en_core_web_sm',
        'de': 'de_core_news_sm',
        'es': 'es_core_news_sm',
        'fr': 'fr_core_news_sm',
        'it': 'it_core_news_sm',
        'nl': 'nl_core_news_sm',
        'pt': 'pt_core_news_sm',
        'ru': 'ru_core_news_sm',
        'zh': 'zh_core_web_sm',      # Chinese
        'ja': 'ja_core_news_sm',     # Japanese
        'pl': 'pl_core_news_sm',     # Polish
        'da': 'da_core_news_sm',     # Danish
        'ro': 'ro_core_news_sm',     # Romanian
        'el': 'el_core_news_sm',     # Greek
        'ca': 'ca_core_news_sm',     # Catalan
        'uk': 'uk_core_news_sm',     # Ukrainian
        'nb': 'nb_core_news_sm',     # Norwegian Bokmål
    }
    
    # 1. Get the specific model name, or default to the multilingual one ('xx')
    model_name = spacy_model_map.get(lang_code, 'xx_ent_wiki_sm')
    
    # 2. Check if we already loaded it into memory
    if model_name not in SPACY_MODELS:
        try:
            # Try to load from hard drive
            SPACY_MODELS[model_name] = spacy.load(model_name)
        except OSError:
            # Not on hard drive? Auto-download it!
            print(f"📦 Auto-downloading spaCy model for language '{lang_code}': {model_name}...")
            try:
                spacy_download(model_name)
                SPACY_MODELS[model_name] = spacy.load(model_name)
                print(f"✅ Successfully loaded {model_name}!")
            except Exception as e:
                print(f"⚠️ Failed to download {model_name}. Error: {str(e)}")
                
                # Double Fallback: If downloading a specific language fails (e.g. network error),
                # try to grab the multilingual model instead before giving up.
                if model_name != 'xx_ent_wiki_sm':
                    print("🔄 Falling back to multilingual model (xx_ent_wiki_sm)...")
                    return get_spacy_model('xx')
                    
                SPACY_MODELS[model_name] = None
                
    return SPACY_MODELS[model_name]

def get_clean_body_soup(html_source):
    """
    Helper Function: Mimics AI web scrapers by stripping out navigation, 
    headers, footers, sidebars, and scripts to isolate the main article text.
    """
    soup = BeautifulSoup(html_source, 'lxml')
    
    # 1. Remove obviously non-content tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'form', 'svg']):
        tag.decompose()
        
    # 2. Remove common CSS classes used for sidebars and menus
    for div in soup.find_all(['div', 'ul', 'section'], class_=re.compile(r'sidebar|menu|widget|nav|footer|header|cookie|popup', re.I)):
        div.decompose()
        
    return soup

def create_webdriver():
    driver = Driver(
            browser="chrome",
            wire=False,
            uc=True,
            headless2=True,
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            locale_code="de",
            no_sandbox=True,
            )
    return driver

def read_config_file(filename):
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    with open(os.path.join(parentdir, filename), 'r') as f:
        return json.load(f)

def _save_robot_txt_selenium(main):
    """Fallback: Uses heavy SeleniumBase to bypass Cloudflare/WAFs if requests is blocked."""
    url = main.rstrip('/') + '/robots.txt'
    if not url.startswith("http"):
        url = "https://" + url

    driver = create_webdriver()
    driver.set_page_load_timeout(10)
    try:
        driver.get(url)
        time.sleep(1)
        code = driver.page_source
        driver.quit()
        return code
    except:
        try:
            driver.quit()
        except:
            pass
        return False

def save_robot_txt(main):
    """Tries lightning-fast requests first. Falls back to Selenium if blocked."""
    url = main.rstrip('/') + '/robots.txt'
    if not url.startswith("http"):
        url = "https://" + url

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        # Check if we got blocked by a WAF (403 Forbidden, 406 Not Acceptable, 503 Service Unavailable)
        if response.status_code in [403, 406, 503]:
            return _save_robot_txt_selenium(main)
            
        # Check if Cloudflare gave us a 200 OK but returned a JS challenge instead of the robots.txt
        response_text = response.text.lower()
        if "cloudflare" in response_text or "just a moment" in response_text or "<html" in response_text:
            return _save_robot_txt_selenium(main)

        # Success via fast requests!
        if response.status_code == 200:
            return response.text
            
        return False
        
    except requests.RequestException:
        # If there's a timeout or connection error with requests, try Selenium as a last resort
        return _save_robot_txt_selenium(main)

def calculate_loading_time(url):
    driver = create_webdriver()
    driver.set_page_load_timeout(10) 
    loading_time = -1

    try:
        driver.get(url)
        navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
        domComplete = driver.execute_script("return window.performance.timing.domContentLoadedEventEnd")
        
        if domComplete > 0:
            loadingTime = domComplete - navigationStart
            loading_time = loadingTime / 1000
        else:
            loading_time = -1
            
        driver.quit()
    except:
        loading_time = -1
        try:
            driver.quit()
        except Exception as e:
            pass
    
    return loading_time

def match_text(text, pattern):
    text = text.lower()
    pattern= pattern.lower()
    return fnmatch.fnmatch(text, pattern)

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except:
        return False

def get_scheme(url):
    return urlparse(url).scheme

def get_netloc(url):
    return urlparse(url).netloc

def get_hyperlinks(source, main):
    hyperlinks = ""
    if source != "error":
        # USE CLEAN SOUP to only get contextual links from the actual article!
        soup = get_clean_body_soup(source)
        
        # Only look for tags that actually have an href attribute
        tags = soup.find_all('a', href=True)

        for tag in tags:
            hyperlink_text = str(tag.string).strip() if tag.string else ""
            href = str(tag.get('href')).strip()
            
            if "http" not in href:
                href = href.lstrip('/')
                href = main.rstrip('/') + '/' + href

            hyperlink = "[url]" + hyperlink_text + "   " + href
            if not match_text(hyperlink, '*mailto:*') and not match_text(hyperlink, '*tel:*'):
                hyperlinks += hyperlink + "\n"

        return hyperlinks

def identify_url_length(url):
    url = url.replace("www.", "")
    if (match_text(url, "https://*")):
        url = url.replace("https://", "")
    elif(match_text(url, "http://*")):
        url = url.replace("http://", "")
    return str(len(url))

def identify_https(url):
    return 1 if get_scheme(url) == 'https' else 0

def identify_micros(source):
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    micros_list = []
    with open(os.path.join(parentdir, 'lists/micro.csv'), 'r') as csvfile:
        micros = csv.reader(csvfile)
        for m in micros:
            micros_list.append((m[0], m[1]))

    micros_found = [ms[0] for ms in micros_list if match_text(source, ms[1])]
    return micros_found

def analyze_microdata_advanced(source):
    score = 0
    source_lower = source.lower()
    if '<script type="application/ld+json">' in source_lower:
        score += 50
    if 'itemscope' in source_lower or 'itemtype' in source_lower or 'itemprop' in source_lower:
        score += 50
    return score

def identify_viewport(source):
    return 1 if match_text(source, '*meta*name*viewport*') else 0

def identify_sitemap(source):
    return 1 if match_text(source, "*a*href*sitemap*") else 0

def identify_canonical(source):
    tree = html.fromstring(source)
    xpath = '//a[@rel="canonical"] | //link[@rel="canonical"]'
    return len(tree.xpath(xpath))

def identify_nofollow(source):
    tree = html.fromstring(source)
    xpath_code = '//a[@rel="nofollow"]'
    hyperlink_counter = len(tree.xpath(xpath_code))

    xpath_robot = '/meta[@name="robots"]/@content'
    hyperlinks_robot = tree.xpath(xpath_robot)

    for hyperlink in hyperlinks_robot:
        if hyperlink == 'nofollow':
            hyperlink_counter += 1

    return hyperlink_counter

def identify_h1(source):
    tree = html.fromstring(source)
    return len(tree.xpath("//h1/text()"))

def identify_h2(source):
    tree = html.fromstring(source)
    return len(tree.xpath("//h2"))

def get_clean_keywords(search_query, nlp_model=None):
    """
    Helper function: Removes stop words and single characters from the search query.
    Automatically adapts to the language of the loaded spaCy model.
    """
    keywords = search_query.split()
    
    if nlp_model:
        # Get language-specific stop words from the loaded spaCy model
        stop_words = nlp_model.Defaults.stop_words
        # Filter out stop words and tiny words (like "a", "I")
        clean_keywords = [kw for kw in keywords if kw.lower() not in stop_words and len(kw) > 1]
    else:
        # Basic English/German fallback if spaCy fails to load
        fallback_stops = {'is', 'a', 'the', 'of', 'for', 'and', 'to', 'in', 'on', 'with', 
                          'der', 'die', 'das', 'und', 'ist', 'für', 'mit', 'zu', 'den', 'dem'}
        clean_keywords = [kw for kw in keywords if kw.lower() not in fallback_stops and len(kw) > 1]
        
    # If the user ONLY entered stop words (e.g. query was literally "to be or not to be"), 
    # fallback to the original words so we don't return an empty list.
    return clean_keywords if clean_keywords else keywords


def identify_keywords_in_source(source, search_query, nlp_model=None):
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    counter = 0
    # USE THE NEW CLEANING FUNCTION
    keywords = get_clean_keywords(search_query, nlp_model)
    tree = html.fromstring(source)

    try:
        with open(os.path.join(parentdir, 'config/kw.ini'), 'r') as f:
            array = json.load(f)
        kw_array = array['keywords']
    except:
        return 0

    for kw in keywords:
        for key, xpath in kw_array.items():
            content = tree.xpath(xpath)
            for c in content:
                if kw.lower() in c.lower():
                    counter += 1
    return counter


def identify_keywords_in_url(url, search_query, nlp_model=None):
    counter = 0
    keywords = get_clean_keywords(search_query, nlp_model)
    
    url_lower = url.lower()
    
    for kw in keywords:
        # Check if the keyword exists as a distinct word in the URL 
        # (e.g. bordered by slashes, hyphens, or dots)
        kw_lower = re.escape(kw.lower())
        if re.search(rf'(?:^|[-/.?=&]){kw_lower}(?:[-/.?=&]|$)', url_lower):
            counter += 1
            
    return counter

def identify_keyword_density(source, search_query, nlp_model=None):
    soup = BeautifulSoup(source, 'lxml')

    if search_query:
        for script in soup(["script", "style"]):
            script.extract()

        raw_text = soup.get_text(separator=' ', strip=True).lower()
        if not raw_text:
            return 0.0

        source_words = re.findall(r'\w+', raw_text)
        w_counter = len(source_words)

        if w_counter == 0:
            return 0.0

        # Get the cleaned core keywords
        clean_keywords = get_clean_keywords(search_query, nlp_model)
        if not clean_keywords:
            return 0.0

        max_density = 0.0
        
        # Calculate density for each core keyword individually
        for kw in set(clean_keywords):
            kw_lower = kw.lower()
            # Use regex boundaries \b so "AI" doesn't match inside "trAIning"
            matches = len(re.findall(rf'\b{re.escape(kw_lower)}\b', raw_text))
            
            density = (matches / w_counter) * 100
            
            # We want to catch the worst offender for the keyword stuffing penalty
            if density > max_density:
                max_density = density
                
        return int(max_density * 100) / 100
    
    return 0.0

def identify_description(source):
    source = source.lower()
    tree = html.fromstring(source)

    xpath_meta = "//meta[@name='description']/@content"
    xpath_og_property = "//meta[@property='og:description']/@content"
    xpath_og_name = "//meta[@name='og:description']/@content"
    xpath_site_description = "//p[@class='site-description']/text()"

    meta_content = str(tree.xpath(xpath_meta))
    og_property_content = str(tree.xpath(xpath_og_property))
    og_name = str(tree.xpath(xpath_og_name))
    site_description = str(tree.xpath(xpath_site_description))

    if len(meta_content) > 5 or len(og_property_content) > 5 or len(og_name) > 5 or len(site_description) > 5:
        return 1
    return 0

def identify_title(source):
    source = source.lower()
    tree = html.fromstring(source)
    
    xpath_title = "//title/text()"
    xpath_meta_title = "//meta[@name='title']/@content"
    xpath_og_title = "//meta[@property='og:title']/@content"
    xpath_site_title = "//p[@class='site-title']/text()"

    check_title = str(tree.xpath(xpath_title))
    check_meta_title = str(tree.xpath(xpath_meta_title))
    check_og_title = str(tree.xpath(xpath_og_title))
    site_title = str(tree.xpath(xpath_site_title))

    if len(check_title) > 2 or len(check_meta_title) > 2  or len(check_og_title) > 2 or len(site_title) > 2:
        return 1
    return 0

# --- FIX 4: HIGH TRUST OUTBOUND LINKS ---
def identify_hyperlinks(hyperlinks, main):
    internal_links = 0
    external_links = 0
    high_trust_links = 0
    link_list = list()
    
    high_trust_tlds = ['.edu', '.gov', '.mil', 'wikipedia.org', 'nature.com', 'sciencedirect.com']

    urls_split = hyperlinks.split("[url]")

    for u in urls_split:
        if "   " in u:
            link_split = u.split("   ")
            link = link_split[-1].strip()
            link_list.append(link)
            
    for href in set(link_list):
        if is_valid_url(href):
            if main in href:
                internal_links += 1
            else:
                external_links += 1
                if any(trust_domain in href.lower() for trust_domain in high_trust_tlds):
                    high_trust_links += 1

    return {'internal': internal_links, 'external': external_links, 'high_trust_links': high_trust_links}

def identify_robots_txt(main):
    result = 0
    try:
        source = save_robot_txt(main)
        if source:
            patterns = ["*gptbot*", "*claudebot*", "*anthropic-ai*", "*ccbot*", "*google-extended*", "*noindex*"]
            for pattern in patterns:
                if match_text(source, pattern):
                    result = 1
                    break
    except:
        result = -1
    return result

def identify_structure_elements(source):
    try:
        # Use the clean soup so we don't count navigation menus!
        soup = get_clean_body_soup(source)
        return {
            'tables': len(soup.find_all('table')),
            'ul_lists': len(soup.find_all('ul')),
            'ol_lists': len(soup.find_all('ol')),
            'list_items': len(soup.find_all('li'))
        }
    except Exception as e:
        print(f"Error in identify_structure_elements: {str(e)}")
        return {'tables': 0, 'ul_lists': 0, 'ol_lists': 0, 'list_items': 0}

def identify_faqs_advanced(source):
    results = {
        'schema_faq_present': 0,
        'schema_qa_count': 0,
        'semantic_qa_count': 0,
        'faq_css_classes': 0
    }
    try:
        soup = BeautifulSoup(source, 'lxml')
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        data = [data]
                    for item in data:
                        if item.get('@type') == 'FAQPage':
                            results['schema_faq_present'] = 1
                            entities = item.get('mainEntity', [])
                            if isinstance(entities, list):
                                results['schema_qa_count'] += len(entities)
                        elif item.get('@type') == 'Question':
                            results['schema_qa_count'] += 1
                except json.JSONDecodeError:
                    continue

        headings = soup.find_all(['h2', 'h3', 'h4', 'strong'])
        for h in headings:
            text = h.get_text().strip()
            if text.endswith('?'):
                next_sibling = h.find_next_sibling()
                if next_sibling and next_sibling.name in ['p', 'div'] and len(next_sibling.get_text().strip().split()) > 5:
                    results['semantic_qa_count'] += 1

        results['faq_css_classes'] = len(soup.find_all(class_=re.compile(r'faq|accordion|question|answer', re.IGNORECASE)))
        return results
    except:
        return results

def analyze_paragraphs(source):
    try:
        # Use the clean soup so we don't count footer/sidebar text!
        soup = get_clean_body_soup(source)
        paragraphs = soup.find_all('p')
        
        if not paragraphs:
            return {'p_count': 0, 'avg_words_per_p': 0, 'avg_sentences_per_p': 0}
            
        total_words = 0
        total_sentences = 0
        valid_p_count = 0
        
        for p in paragraphs:
            text = p.get_text(separator=' ', strip=True)
            words = text.split()
            
            # Skip "UI" paragraphs (usually 1 to 5 words long like "Read More" or "Copyright")
            if len(words) > 5:
                total_words += len(words)
                total_sentences += max(1, len(re.split(r'[.!?]+', text)) - 1)
                valid_p_count += 1
                
        if valid_p_count == 0:
            return {'p_count': 0, 'avg_words_per_p': 0, 'avg_sentences_per_p': 0}
            
        return {
            'p_count': valid_p_count,
            'avg_words_per_p': round(total_words / valid_p_count, 2),
            'avg_sentences_per_p': round(total_sentences / valid_p_count, 2)
        }
    except Exception as e:
        print(f"Error in analyze_paragraphs: {str(e)}")
        return {'p_count': 0, 'avg_words_per_p': 0, 'avg_sentences_per_p': 0}

def analyze_readability(source, lang_code='en'):
    try:
        soup = BeautifulSoup(source, 'lxml')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        if not text:
            return 0
            
        textstat.set_lang(lang_code)
        return textstat.flesch_reading_ease(text)
    except:
        return 0

def identify_authority_signals(source):
    try:
        tree = html.fromstring(source)
        
        soup = get_clean_body_soup(source)
        text = soup.get_text(separator=' ', strip=True)
        
        quotes_count = len(re.findall(r'["\'„“«»""]', text))
        
        return {
            'blockquotes': len(tree.xpath('//blockquote')),
            'author_tags': len(tree.xpath('//*[@rel="author"]')) + len(tree.xpath('//meta[@name="author"]')),
            'quotes_count': quotes_count 
        }
    except:
        return {'blockquotes': 0, 'author_tags': 0, 'quotes_count': 0} 

def analyze_company_signals(source):
    signals = 0
    source_lower = source.lower()
    if '"@type": "organization"' in source_lower or '"@type": "publisher"' in source_lower or '"sameas"' in source_lower:
        signals += 1
    try:
        soup = BeautifulSoup(source, 'lxml')
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text().lower()
            if 'impressum' in footer_text or 'about' in footer_text or 'über uns' in footer_text:
                signals += 1
    except:
        pass
    return signals

def identify_statistics_and_entities_universal(source, nlp_model):
    results = {'percentage_count': 0, 'year_count': 0, 'organizations_count': 0}
    try:
        if nlp_model is None:
            return results
            
        soup = BeautifulSoup(source, 'lxml')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # 1. UNIQUE Percentages: Only count distinct statistics
        percentages = re.findall(r'\d+(?:[.,]\d+)?\s*%', text)
        results['percentage_count'] = len(set(percentages))
        
        # 2. UNIQUE Years: Restrict to a realistic historical range (1950-2039)
        # This automatically drops duplicates (e.g. 50 mentions of "2024" becomes 1)
        years = re.findall(r'\b(?:19[5-9]\d|20[0-3]\d)\b', text)
        results['year_count'] = len(set(years))
        
        # 3. Entities (Organizations, People, Locations)
        doc = nlp_model(text[:100000])
        
        # Using a set here as well is highly recommended! 
        # Mentioning "Google" 100 times is keyword stuffing. 
        # Mentioning "Google, Microsoft, OpenAI, Apple" shows real authority.
        unique_entities = set(ent.text.lower() for ent in doc.ents if ent.label_ in ['ORG', 'PER', 'LOC'])
        results['organizations_count'] = len(unique_entities)
        
        return results
    except Exception as e:
        print(f"Error in identify_statistics_and_entities_universal: {str(e)}")
        return results

def extract_clean_text_for_ngrams(html_content):
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        return soup.get_text(separator=' ', strip=True)
    except:
        return ""

# --- FIX 1: Vector Overlap Calculation ---
def analyze_multi_source_overlap_semantic(ai_segment_text, sources_dict):
    """
    Compares AI generated text with sources using Sentence Embeddings (Cosine Similarity).
    """
    if not ai_segment_text or not sources_dict:
        return {}

    results = {}
    
    # Fallback if sentence_transformers isn't installed
    if EMBEDDING_MODEL is None:
        for src_id in sources_dict.keys():
            results[src_id] = {'semantic_similarity_percentage': 0.0}
        return results

    try:
        ai_embedding = EMBEDDING_MODEL.encode([ai_segment_text])
        
        for src_id, html_code in sources_dict.items():
            clean_text = extract_clean_text_for_ngrams(html_code)
            if not clean_text:
                results[src_id] = {'semantic_similarity_percentage': 0.0}
                continue
                
            # Chunk the source text (generative models chunk texts similarly)
            words = clean_text.split()
            chunks = [' '.join(words[i:i+150]) for i in range(0, len(words), 150)]
            if not chunks:
                results[src_id] = {'semantic_similarity_percentage': 0.0}
                continue
                
            chunk_embeddings = EMBEDDING_MODEL.encode(chunks)
            similarities = cosine_similarity(ai_embedding, chunk_embeddings)[0]
            max_sim = max(similarities)
            
            # Convert cosine similarity (-1 to 1) into a percentage
            sim_pct = max(0, min(100, round(max_sim * 100, 2)))
            results[src_id] = {'semantic_similarity_percentage': sim_pct}
            
    except Exception as e:
        print(f"Error in vector similarity: {e}")
        for src_id in sources_dict.keys():
            results[src_id] = {'semantic_similarity_percentage': 0.0}
            
    return results

if __name__ == "__main__":
    pass