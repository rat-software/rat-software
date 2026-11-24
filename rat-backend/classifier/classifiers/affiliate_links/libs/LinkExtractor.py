from bs4 import BeautifulSoup
from functools import lru_cache
import json
import os
import re
#test
import requests

@lru_cache(maxsize=8589934592)
def resolve_url(link):
    try:
        response = requests.head(link, allow_redirects=True, timeout=1) #timeout verkürzen falls zu lange dauert
        return response.url
    except requests.RequestException as e:
        #print(f"Fehler beim Auflösen des Links {link}: {e}")
        return link

def extract_affiliate_links(html_content):    
    soup = BeautifulSoup(html_content, 'html.parser')

    # Finde alle <a>-Tags
    a_tags = soup.find_all('a', href=True)
    #print("A_Tags:" + str(len(a_tags)))
    
    # Liste für Affiliate-Links mit Tags
    affiliate_links_with_tags = []
    
    # Überprüfe jeden <a>-Tag
    for tag in a_tags:
        # Only tags with a rel attribute containing "sponsored", "nofollow" or "noopener"
        # can be affiliate links; skip all others before any (expensive) URL resolution
        if not check_rel(tag):
            continue

        link = tag['href']
        if is_affiliate_link_regexp(link):
            # Speichere den Link und den gesamten <a>-Tag als String
            affiliate_links_with_tags.append({'link': link, 'tag': str(tag), 'location': get_parent_tags(tag)})
        else:
            #print("resolving: "+ str(link))
            resolved_link = resolve_url(link)  # Link vor der Überprüfung auflöse
            if is_affiliate_link_regexp(resolved_link):
                # Speichere den Link und den gesamten <a>-Tag als String
                affiliate_links_with_tags.append({'link': resolved_link, 'tag': str(tag), 'location': get_parent_tags(tag)})

    # Gib die gefundenen Affiliate-Links zurück
    return affiliate_links_with_tags

def getTextLength(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Nur den Textinhalt extrahieren
    text_content = soup.get_text()
    # Länge des Textinhalts
    text_content_length = len(text_content)

    return text_content_length

def check_rel(tag):
    if ('rel' in tag.attrs and any(keyword in tag['rel'] for keyword in ["sponsored", "nofollow", "noopener"])):
        return True
    else:
        return False

def get_parent_tags(tag):
    parents = []
    parent = tag.find_parent()
    while parent is not None:
        parents.append(parent.name)
        parent = parent.find_parent()
    return parents

# Affiliate networks with their detection pattern and example links, loaded from
# config/affiliate_networks.json. Patterns are matched with re.search() against the
# (resolved) link, in list order.
AFFILIATE_NETWORKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'affiliate_networks.json')

def load_affiliate_networks(path=AFFILIATE_NETWORKS_FILE):
    """
    Load the affiliate networks from the JSON config file and compile their patterns.

    Args:
        path (str): Path to the JSON file.

    Returns:
        list[dict]: Networks with key, name, pattern, examples and compiled regex.
    """
    with open(path, 'r', encoding='utf-8') as f:
        networks = json.load(f)
    for network in networks:
        network["regex"] = re.compile(network["pattern"])
    return networks

AFFILIATE_NETWORKS = load_affiliate_networks()

def get_affiliate_network(link):
    """
    Determine the affiliate network of a link.

    Args:
        link (str): The URL to check.

    Returns:
        str | None: The key of the first matching network (e.g. "amazon"), or None.
    """
    if not link:
        return None
    for network in AFFILIATE_NETWORKS:
        if network["regex"].search(link):
            return network["key"]
    return None

def is_affiliate_link_regexp(link):
    """
    Check whether a link is an affiliate link using the AFFILIATE_NETWORKS patterns.

    Args:
        link (str): The URL to check.

    Returns:
        bool: True if the link matches a known affiliate network pattern.
    """
    return get_affiliate_network(link) is not None
