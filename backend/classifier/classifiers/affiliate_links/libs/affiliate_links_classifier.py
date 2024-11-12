from bs4 import BeautifulSoup
import requests
from functools import lru_cache
import json
import os

'''
This classifier allows users to extract affiliate links embedded in web pages

'''


# Check if the link matches affiliate patterns
def is_affiliate_link(link):
    keyword_sets = [
        ["https://", "amazon", "tag="],
        ["https://", "amazon", "tag%3D"],
        ["https://", "tag="],
        ["https://", "awin1"],
        ["https://", "ebay", "mkcid"],
        ["https://", "aliexpress", "click", "e"],
        ["https://", "bestcheck", "track"],
        ["https://", "shareasale", "r.cfm"],
        ["https://", "shrsl"],
        ["https://", "clickbank", "hop"],
        ["https://", "jdoqocy", "click"],
        ["https://", "anrdoezrs", "links"],
        ["https://", "flexlinks", "track", "a.ashx"],
        ["https://", "rfsn"],
        ["https://", "linksynergy", "t"],
        ["https://", "itunes", "apple"],
        ["https://", "play", "google"],
        ["https://", "webgains", "track", "click"],
        ["https://", "gutscheine"],
    ]
    
    for keyword_set in keyword_sets:
        if all(keyword in link for keyword in keyword_set):
            return True
    return False


def check_rel(tag):
    return 'rel' in tag.attrs and any(keyword in tag['rel'] for keyword in ["sponsored", "nofollow", "noopener"])


@lru_cache(maxsize=8589934592)
def resolve_url(link):
    try:
        response = requests.head(link, allow_redirects=True, timeout=1)
        return response.url
    except requests.RequestException:
        return link


def get_parent_tags(tag):
    parents = []
    parent = tag.find_parent()
    while parent is not None:
        parents.append(parent.name)
        parent = parent.find_parent()
    return parents


def extract_affiliate_links(html_content):    
    soup = BeautifulSoup(html_content, 'html.parser')
    a_tags = soup.find_all('a', href=True)
    #print(f"Total <a> tags found: {len(a_tags)}")  # Debugging line
    affiliate_links_with_tags = []

    for tag in a_tags:
        link = tag['href']
        #print(f"Checking link: {link}")  # Debugging line
        
        if (is_affiliate_link(link) and check_rel(tag)):
            affiliate_links_with_tags.append({'link': link, 'tag': str(tag), 'location': get_parent_tags(tag)})
        else:
            resolved_link = resolve_url(link)  
            if (is_affiliate_link(resolved_link) and check_rel(tag)):
                affiliate_links_with_tags.append({'link': resolved_link, 'tag': str(tag), 'location': get_parent_tags(tag)})

    return affiliate_links_with_tags

# Main function to classify and extract affiliate links
def classify_result(code, url):
    web_content = code
    
    soup = BeautifulSoup(web_content, 'html.parser')
    affiliate_links = extract_affiliate_links(web_content)
    
    text_content = soup.get_text()
    length = len(text_content)

    return calculate_points(affiliate_links, url, length)
    
container_tags = {'nav': 1,'footer': 2, 'main': 3, 'section': 4, 'header': 5, 'aside': 6,  'article': 7}


def calculate_points(affiliate_links, url, length):
    total_rep_points = 0  
    total_locations_points = 0
    for item in affiliate_links:
       
        class_count = (len(item.get('tag', '').split('class="')) - 1)
        img_count = (item.get('tag', '').count('<img '))
        style_count = item.get('tag', '').count('style=')
        h_tag_count = sum(item.get('tag', '').count('<h{0}'.format(i)) for i in range(1, 7))
        location_points = 0
        for tags in container_tags:
            if tags in item.get('location'):
                location_points += container_tags[tags]

     
        rep_points = class_count*0.5 + img_count*2 + style_count + h_tag_count
        item['class_count'] = class_count 
        item['img_count'] = img_count 
        item['style_count'] = style_count 
        item['h_tag_count'] = h_tag_count 
        item['rep_points'] = rep_points
        item['loc_points'] = location_points        

      
        total_rep_points += rep_points  
        total_locations_points += location_points

    
    average_rep_points = total_rep_points / len(affiliate_links) if affiliate_links else 0
    average_locations_points = total_locations_points / len(affiliate_links) if affiliate_links else 0

    score = len(affiliate_links) + average_rep_points + 2*average_locations_points
    relScore = (score / length) if length else 0
    
    result = [
        {'Link': {'url/path': url}},
        {'Affiliate Links': len(affiliate_links)}, 
        {'Average Highlighting Strength': average_rep_points}, 
        {'Average Position': average_locations_points}, 
        {'Score': score},
        {'textLength': length},
        {'relScore': relScore*10000}
    ]
    
    return result

