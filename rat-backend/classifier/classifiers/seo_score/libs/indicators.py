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
import requests

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
            #mobile=True,
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
    driver.set_page_load_timeout(10) # Bricht nach 10 Sekunden gnadenlos ab[cite: 13]
    loading_time = -1

    try:
        driver.get(url)
        # HINWEIS: Das time.sleep(1) wurde hier entfernt, da driver.get() ohnehin blockiert, 
        # bis die Seite geladen ist. Wir sparen uns 1 Sekunde Wartezeit pro URL!
        
        navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
        # FIX: Wir nutzen domContentLoadedEventEnd statt loadEventEnd. 
        # Das misst die Zeit, bis der reine Text/HTML-Code da ist!
        domComplete = driver.execute_script("return window.performance.timing.domContentLoadedEventEnd")
        
        # Sicherheits-Check: Falls der DOM noch nicht da ist (z.B. bei Blockaden), ist der Wert 0
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
    """
    Function to check if a text matches a pattern using wildcard characters.

    Args:
        text (str): The text to check.
        pattern (str): The pattern to match against.

    Returns:
        bool: True if the text matches the pattern, False otherwise.
    """
    text = text.lower()
    pattern= pattern.lower()
    check = fnmatch.fnmatch(text, pattern)
    return check

def is_valid_url(url):
    """
    Function to check if a URL is valid.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except:
        return False

def get_scheme(url):
    """
    Function to get the scheme (http or https) of a URL.

    Args:
        url (str): The URL to get the scheme from.

    Returns:
        str: The scheme of the URL.
    """
    parsed = urlparse(url)
    return parsed.scheme

def get_netloc(url):
    """
    Function to get the netloc (domain) of a URL.

    Args:
        url (str): The URL to get the netloc from.

    Returns:
        str: The netloc of the URL.
    """
    parsed = urlparse(url)
    return parsed.netloc

def get_hyperlinks(source, main):
    """
    Function to extract hyperlinks from the source code of a webpage.

    Args:
        source (str): The source code of the webpage.
        main (str): The main URL of the website.

    Returns:
        str: The extracted hyperlinks.
    """
    hyperlinks = ""

    if source !="error":
        #extract all comments in source code
        soup = BeautifulSoup(source, 'lxml')

        soup_urls = []
        tags = soup.find_all('a')

        for tag in tags:
            hyperlink_text = str(tag.string).strip()
            href = str(tag.get('href')).strip()
            if "http" not in href:
                href = href.lstrip('/')
                href = main+href

            hyperlink = "[url]"+hyperlink_text+"   "+href
            if not match_text(hyperlink, '*mailto:*'):
                if hyperlink and hyperlink != " ":
                    hyperlinks = hyperlinks+hyperlink

        return hyperlinks

def get_plugins():
    """
    Function to get the list of plugins from the configuration file.

    Returns:
        list: The list of plugins.
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    with open(os.path.join(parentdir, 'config/evaluation.ini'), 'r') as f:
        array = json.load(f)

    plugins_json = array["text-match"]
    plugins = []

    

    for get_plugin in plugins_json:
        name = get_plugin
        source = plugins_json[name]["source"]
        source_dir = parentdir+source
        with open(source_dir, 'r') as csvfile:
            csv_result = csv.reader(csvfile, delimiter=',', quotechar='"')
            source = list(csv_result)
        plugin = {
        "name": name,
        "source": source
        }
        plugins.append(plugin)

    return plugins


def identify_url_length(url):
    """
    Function to identify the length of a URL.

    Args:
        url (str): The URL to identify the length of.

    Returns:
        str: The length of the URL.
    """
    result = -1
    url = url.replace("www.", "")

    if (match_text(url, "https://*")):
        url = url.replace("https://", "")

    elif(match_text(url, "http://*")):
        url = url.replace("http://", "")

    result = str(len(url))

    return result

def identify_https(url):
    """
    Function to identify if a URL uses HTTPS.

    Args:
        url (str): The URL to identify.

    Returns:
        int: 1 if the URL uses HTTPS, 0 otherwise.
    """
    scheme = get_scheme(url)
    result = 0

    if scheme == 'https':
        result = 1

    return result

def identify_micros(source):
    """
    Function to identify microdata/microformats in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        list: The list of identified microdata/microformats.
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    micros_list = []
    with open(os.path.join(parentdir, 'lists/micro.csv'), 'r') as csvfile:
        micros = csv.reader(csvfile)
        for m in micros:
            module = m[0]
            pattern = m[1]
            item = (module, pattern)
            micros_list.append(item)

    micros_found = []

    for ms in micros_list:
        obj = ms[0]
        pattern = ms[1]

        if match_text(source, pattern):
            micros_found.append(obj)

    return micros_found

def identify_og(source):
    """
    Function to identify if Open Graph tags are present in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: 1 if Open Graph tags are present, 0 otherwise.
    """
    pattern = '<*meta*og:*>'
    result = 0

    if match_text(source, pattern):
        result = 1

    return result

def identify_viewport(source):
    """
    Function to identify if a viewport meta tag is present in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: 1 if a viewport meta tag is present, 0 otherwise.
    """
    pattern = '*meta*name*viewport*'
    result = 0

    if match_text(source, pattern):
        result = 1

    return result

def identify_sitemap(source):
    """
    Function to identify if a sitemap link is present in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: 1 if a sitemap link is present, 0 otherwise.
    """
    pattern = "*a*href*sitemap*"
    result = 0

    if (match_text(source, pattern)):
        result = 1

    return result

def identify_wordpress(source):
    """
    Function to identify if a webpage is built with WordPress based on the source code.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: 1 if the webpage is built with WordPress, 0 otherwise.
    """
    tree = html.fromstring(source)
    xpath = "//meta[@name='generator']/@content"
    content = tree.xpath(xpath)
    check = str(content)
    check = check.lower()

    result = 0

    if len(check) > 1:
        pattern = "*wordpress*"
        if match_text(check, pattern):
            result = 1

    return result

def identify_canonical(source):
    """
    Function to identify the number of canonical links in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: The number of canonical links.
    """
    tree = html.fromstring(source)
    xpath = '//a[@rel="canonical"] | //link[@rel="canonical"]'
    hyperlink_counter = 0

    hyperlinks = tree.xpath(xpath)

    for hyperlink in hyperlinks:
        hyperlink_counter = hyperlink_counter + 1

    return hyperlink_counter

def identify_nofollow(source):
    """
    Function to identify the number of nofollow links in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: The number of nofollow links.
    """
    tree = html.fromstring(source)
    xpath_code = '//a[@rel="nofollow"]'
    hyperlink_counter = 0

    hyperlinks_code = tree.xpath(xpath_code)

    for hyperlink in hyperlinks_code:
        hyperlink_counter = hyperlink_counter + 1

    xpath_robot = '/meta[@name="robots"]/@content'

    hyperlinks_robot = tree.xpath(xpath_robot)

    for hyperlink in hyperlinks_robot:
        if hyperlink == 'nofollow':
            hyperlink_counter = hyperlink_counter + 1

    return hyperlink_counter

def identify_h1(source):
    """
    Function to identify the number of H1 tags in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: The number of H1 tags.
    """
    tree = html.fromstring(source)
    xpath = "//h1/text()"
    counter = 0
    res = tree.xpath(xpath)

    for r in res:
        counter = counter + 1

    return counter

def identify_keywords_in_source(source, search_query):
    """
    Function to identify the number of occurrences of keywords in the source code of a webpage.

    Args:
        source (str): The source code of the webpage.
        search_query (str): The search query containing the keywords.

    Returns:
        int: The number of occurrences of keywords.
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    counter = 0

    keywords = search_query.split()

    tree = html.fromstring(source)

    with open(os.path.join(parentdir, 'config/kw.ini'), 'r') as f:
        array = json.load(f)

    kw_array = array['keywords']

    for kw in keywords:

        for key, xpath in kw_array.items():
            content = tree.xpath(xpath)

            for c in content:
                if kw.lower() in c.lower():
                    counter = counter + 1

    return counter

def identify_keywords_in_url(url, search_query):
    """
    Function to identify the number of occurrences of keywords in a URL.

    Args:
        url (str): The URL to check.
        search_query (str): The search query containing the keywords.

    Returns:
        int: The number of occurrences of keywords.
    """
    counter = 0

    keywords = search_query.split()

    for kw in keywords:
        if kw.lower() in url.lower():
            counter = counter + 1

    return counter

def identify_keyword_density(source, search_query):
    soup = BeautifulSoup(source, 'lxml')
    kw_density = 0.0

    if search_query:
        for script in soup(["script", "style"]):
            script.extract()

        # 1. Text und Query bereinigen 
        # (Wandelt alles in Kleinbuchstaben um und normalisiert Zeilenumbrüche/mehrfache Leerzeichen zu einem)
        raw_text = soup.get_text(separator=' ', strip=True).lower()
        text = ' '.join(raw_text.split())
        query_lower = ' '.join(search_query.lower().split())
        
        if not query_lower or not text:
            return 0.0

        # 2. Gesamtwörter im Text zählen 
        # Wir nutzen \w+ (Wortzeichen), das unterstützt automatisch alle Unicode-Schriftzeichen 
        # (inklusive japanischer Kanji/Kana, kyrillisch, etc.)
        import re
        source_words = re.findall(r'\w+', text)
        w_counter = len(source_words)

        # Fallback für Sonderfälle (z.B. extrem exotische Zeichen ohne regex-Treffer)
        if w_counter == 0:
            w_counter = max(1, len(text))
            query_words_len = len(query_lower)
        else:
            query_words_len = max(1, len(re.findall(r'\w+', query_lower)))

        # 3. EXAKTES Phrase-Matching (Sprachenunabhängig!)
        # Wir suchen nach der genauen Phrase im Fließtext. 
        kw_counter = text.count(query_lower)

        # 4. Berechnung der Dichte 
        # (Anzahl der Phrasen-Treffer * Wörter in der Phrase) / Gesamtwörter des Textes
        kw_density = (kw_counter * query_words_len) / w_counter * 100
            
        decimals = 2
        multiplier = 10 ** decimals
        kw_density = int(kw_density * multiplier) / multiplier

        return kw_density
    
    return 0.0

def identify_description(source):
    """
    Function to identify if a webpage has a meta description.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: 1 if a meta description is present, 0 otherwise.
    """
    source = source.lower()

    tree = html.fromstring(source)

    result = 0

    xpath_meta = "//meta[@name='description']/@content"
    xpath_og_property = "//meta[@property='og:description']/@content"
    xpath_og_name = "//meta[@name='og:description']/@content"
    xpath_site_description = "//p[@class='site-description']/text()"

    meta_content = str(tree.xpath(xpath_meta))
    og_property_content = str(tree.xpath(xpath_og_property))
    og_name = str(tree.xpath(xpath_og_name))
    site_description = str(tree.xpath(xpath_site_description))

    if(len(meta_content) > 5 or len(og_property_content) > 5 or len(og_name) > 5 or len(site_description) > 5):
        result = 1

    return result

def identify_title(source):
    """
    Function to identify if a webpage has a title.

    Args:
        source (str): The source code of the webpage.

    Returns:
        int: 1 if a title is present, 0 otherwise.
    """
    source = source.lower()
    tree = html.fromstring(source)
    result = 0
    xpath_title = "//title/text()"
    xpath_meta_title = "//meta[@name='title']/@content"
    xpath_og_title = "//meta[@property='og:title']/@content"
    xpath_site_title = "//p[@class='site-title']/text()"

    check_title = str(tree.xpath(xpath_title))
    check_meta_title = str(tree.xpath(xpath_meta_title))
    check_og_title = str(tree.xpath(xpath_og_title))
    site_title = str(tree.xpath(xpath_site_title))

    if len(check_title) > 2 or len(check_meta_title) > 2  or len(check_og_title) > 2 or len(site_title) > 2:
        result = 1

    return result

def identify_hyperlinks(hyperlinks, main):
    """
    Function to identify the number of internal and external hyperlinks in a webpage.

    Args:
        hyperlinks (str): The extracted hyperlinks from the webpage.
        main (str): The main URL of the website.

    Returns:
        dict: The number of internal and external hyperlinks.
    """
    link = ""
    internal_links = 0
    external_links = 0
    i = 0
    e = 0
    link_list = list()

    urls_split = hyperlinks.split("[url]")

    for u in urls_split:

        link_split = u.split("   ")
        link = (link_split[-1])
        link_list.append(link)
    link_list.sort()

    for href in link_list:
        if is_valid_url(href):
            if main in href:
                internal_links = internal_links + 1
            else:
                external_links = external_links + 1

    i = internal_links
    e = external_links

    hyper_links_counter = {'internal': i, 'external': e}

    return hyper_links_counter

def identify_plugins(source):
    """
    Function to identify the plugins used in a webpage based on the source code.

    Args:
        source (str): The source code of the webpage.

    Returns:
        dict: The identified plugins.
    """
    plugins = get_plugins()
    found_plugins = {}

    for plugin in plugins:
        plugin_type = plugin['name']
        plugin_list = plugin['source']
        plugin_names = []

        for get_plugin in plugin_list:
            plugin_name = get_plugin[0]
            plugin_search_pattern = get_plugin[1]

            if match_text(source, plugin_search_pattern):
                plugin_names.append(plugin_name)

            update = {plugin_type:plugin_names}
            found_plugins.update(update)

    return found_plugins



def identify_robots_txt(main):
    """
    Function to identify if a webpage has a robots.txt file.

    Args:
        main (str): The main URL of the website.

    Returns:
        int: 1 if a robots.txt file is present, 0 otherwise.
    """
    result = 0

    try:
        source = save_robot_txt(main)
        if source:

            pattern = "*crawl-delay*"
            if match_text(source, pattern):
                result = 1

            pattern = "*user agent*"
            if match_text(source, pattern):
                result = 1

            pattern = "*user-agent*"
            if match_text(source, pattern):
                result = 1

            pattern = "*sitemap*"
            if match_text(source, pattern):
                result = 1

            pattern = "*noindex*"
            if match_text(source, pattern):
                result = 1

            pattern = "*seo*"
            if match_text(source, pattern):
                result = 1

    except:
        result = -1

    return result


if __name__ == "__main__":
    save_robot_txt("https://www.searchstudies.org/")