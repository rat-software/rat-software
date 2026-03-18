from bs4 import BeautifulSoup
import logging

class DynamicParser:
    """
    A generic parser that extracts Search Engine Results and AI Overviews
    from HTML based on dynamically configured CSS selectors.
    """
    
    @staticmethod
    def parse_html(html_content, engine_config):
        """
        Parses the HTML content using the provided SearchEngine configuration.
        
        Args:
            html_content (str): The raw HTML of the SERP.
            engine_config (SearchEngine): The database model containing the CSS selectors.
            
        Returns:
            dict: Contains 'ai_overview' (str), 'ai_sources' (list of dicts), and 'organic' (list of dicts).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        parsed_data = {
            "ai_overview": None,
            "ai_sources": [],
            "organic": []
        }
        
        # ---------------------------------------------------------
        # 1. Parse AI Overview Text
        # ---------------------------------------------------------
        if engine_config.sel_ai_text:
            try:
                ai_elem = soup.select_one(engine_config.sel_ai_text)
                if ai_elem:
                    parsed_data["ai_overview"] = ai_elem.get_text(separator=' ', strip=True)
            except Exception as e:
                logging.error(f"Error parsing AI Text for {engine_config.name}: {e}")

        # ---------------------------------------------------------
        # 2. Parse AI Sources
        # ---------------------------------------------------------
        if engine_config.sel_ai_source_container and engine_config.sel_ai_source_url:
            try:
                source_containers = soup.select(engine_config.sel_ai_source_container)
                for container in source_containers:
                    url_elem = container.select_one(engine_config.sel_ai_source_url)
                    if url_elem and url_elem.has_attr('href'):
                        parsed_data["ai_sources"].append({
                            "url": url_elem['href']
                        })
            except Exception as e:
                logging.error(f"Error parsing AI Sources for {engine_config.name}: {e}")

        # ---------------------------------------------------------
        # 3. Parse Organic Results
        # ---------------------------------------------------------
        if engine_config.sel_container:
            try:
                containers = soup.select(engine_config.sel_container)
                
                for rank, container in enumerate(containers, start=1):
                    # Extract Title
                    title = ""
                    if engine_config.sel_title:
                        title_elem = container.select_one(engine_config.sel_title)
                        title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Extract URL
                    url = ""
                    if engine_config.sel_url:
                        url_elem = container.select_one(engine_config.sel_url)
                        url = url_elem['href'] if url_elem and url_elem.has_attr('href') else ""
                        
                    # Extract Snippet
                    snippet = ""
                    if engine_config.sel_snippet:
                        snippet_elem = container.select_one(engine_config.sel_snippet)
                        snippet = snippet_elem.get_text(separator=' ', strip=True) if snippet_elem else ""
                    
                    # Only append if we at least found a URL or Title
                    if url or title:
                        parsed_data["organic"].append({
                            "rank": rank,
                            "title": title[:255], # Ensure it fits in DB
                            "url": url,
                            "snippet": snippet
                        })
            except Exception as e:
                logging.error(f"Error parsing Organic Results for {engine_config.name}: {e}")

        return parsed_data