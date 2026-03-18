from bs4 import BeautifulSoup
import logging
import urllib

class DynamicParser:
    @staticmethod
    def parse_html(html_content, config, debug_logs=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        def log_msg(msg):
            if debug_logs is not None:
                debug_logs.append(msg)
            logging.info(msg)

        parsed_data = {
            "ai_overview": None,
            "ai_sources": [],
            "organic": [],
            "has_next_page": False
        }

        print(parsed_data)
        
        # 1. Clean inputs (Restored sel_next_button!)
        sel_container = config.get('sel_container', '').strip()
        sel_title = config.get('sel_title', '').strip()
        sel_url = config.get('sel_url', '').strip()
        sel_snippet = config.get('sel_snippet', '').strip()
        sel_next_button = config.get('sel_next_button', '').strip()
        url_param_decoder = config.get('url_param_decoder', '').strip() 

        # 2. Organic Results
        if sel_container:
            try:
                containers = soup.select(sel_container)
                for rank, container in enumerate(containers, start=1):
                    title_elem = container.select_one(sel_title) if sel_title else None
                    url_elem = container.select_one(sel_url) if sel_url else None
                    
                    # Smart Fallback for DuckDuckGo (Title is also the URL)
                    if not url_elem and title_elem and title_elem.name == 'a':
                        url_elem = title_elem
                    elif not url_elem and title_elem and title_elem.parent and title_elem.parent.name == 'a':
                        url_elem = title_elem.parent
                        
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    url = url_elem.get('href', '') if url_elem else ""

                    # --- NEW: Dynamic URL Decoder ---
                    if url_param_decoder and url_param_decoder in url:
                        try:
                            # Parse the URL and extract the hidden query parameter
                            parse_target = url if url.startswith('http') else 'https:' + url
                            parsed_url = urllib.parse.urlparse(parse_target)
                            qs = urllib.parse.parse_qs(parsed_url.query)
                            if url_param_decoder in qs:
                                url = qs[url_param_decoder][0] # Extract the clean URL
                        except Exception as e:
                            log_msg(f"Failed to decode URL: {e}")
                    
                    # Clean up the protocol for display if it's missing
                    if url and url.startswith('//'):
                        url = 'https:' + url

                    
                    snippet_elem = container.select_one(sel_snippet) if sel_snippet else None
                    snippet = snippet_elem.get_text(separator=' ', strip=True) if snippet_elem else ""
                    
                    if url or title:
                        parsed_data["organic"].append({
                            "rank": rank, "title": title[:255], "url": url, "snippet": snippet
                        })
            except Exception as e:
                log_msg(f"Parser Error: {str(e)}")

        # 3. Next Page Button (Restored!)
        if sel_next_button:
            try:
                next_elem = soup.select_one(sel_next_button)
                parsed_data["has_next_page"] = True if next_elem else False
            except Exception as e:
                log_msg(f"Error parsing Next Button: {e}")

        return parsed_data