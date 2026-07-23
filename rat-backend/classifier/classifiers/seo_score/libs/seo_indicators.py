def analyze_content_length(soup):
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

def analyze_heading_structure(soup):
    """Analyze heading structure and return score"""
    score = 0
    if len(soup.find_all('h1')) == 1:
        score += 40
    if soup.find_all(['h2', 'h3']):
        score += 30
    if soup.find_all(['h4', 'h5', 'h6']):
        score += 30
    return score

def analyze_link_quality(internal_links, external_links):
    """Analyze link quality and structure"""

    score = 0
    total_links = internal_links + external_links

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

    return score

def analyze_images(soup):
    """Calculate percentage of images with alt text"""
    images = soup.find_all('img')
    if not images:
        return 0
    images_with_alt = len([img for img in images if img.get('alt')])
    return round((images_with_alt / len(images)) * 100)

def analyze_navigation(soup):
    """Analyze navigation structure"""
    score = 0
    if soup.find(['nav', 'menu']):
        score += 40
    if soup.find('footer'):
        score += 30
    if soup.find('form'):
        score += 30
    return score

def analyze_title(soup):
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

def analyze_description(soup):
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

def check_social_tags(soup):
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

def analyze_keyword_usage(soup, url, query):
    """Analyze keyword usage in content"""
    if not query:
        return analyze_general_content_optimization(soup)
    return analyze_specific_keyword(soup, url, query)

def analyze_general_content_optimization(soup):
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

def analyze_specific_keyword(soup, url, query):
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