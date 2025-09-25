from scrapers.requirements import *

import csv
import os
import inspect
from pathlib import Path
import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent


def run(query, limit, scraping, headless):
    """
    Scrapes Google search results based on the provided query.

    Args:
        query (str): The search query to use.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class used for encoding and taking screenshots.
        headless (bool): If True, run the browser in headless mode (without GUI).

    Returns:
        list: A list of search results, where each result is a list containing the title, description, URL, 
              and metadata (encoded page source and screenshot binary). Returns -1 if CAPTCHA is detected 
              or if an error occurs during scraping.
    """
    # Initialize variables
    driver = None
    search_results = -1
    max_retries = 3
    retry_count = 0
    used_proxies = set()  # Set to track used proxies
    
    # Load all available proxies
    def load_proxies():
        all_proxies = []
        # Get the directory path to locate the proxy file
        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        
        # Load proxies from a CSV file
        with open(os.path.join(currentdir, 'proxies', 'Sweden.csv')) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                all_proxies.append(row[0])
                
        print(f"Loaded {len(all_proxies)} proxies from file")
        return all_proxies
    
    # All available proxies
    all_proxies = load_proxies()

    # Function to get a random proxy not used before
    def get_proxy():
        available_proxies = [p for p in all_proxies if p not in used_proxies]
        
        if not available_proxies:
            print("WARNING: All proxies have been used. Resetting proxy list.")
            used_proxies.clear()
            available_proxies = all_proxies
            
        # Shuffle and select one
        random.shuffle(available_proxies)
        proxy = available_proxies[0] if available_proxies else None
        
        if proxy:
            used_proxies.add(proxy)
            
        return proxy

    # Define constants for scraping
    search_url = "https://www.google.se/webhp?hl=sv&gl=SE&uule=w+CAIQICIMU3dlZGVuLCBMdW5k"  # URL for Google search
    search_box = "q"  # Name attribute of the search input box
    captcha = "g-recaptcha"  # Indicator for CAPTCHA presence
    next_page_xpath = "//a[@aria-label='{}']"  # XPath template for the "next" button
    next_scroll_xpath = "//span[@class='RVQdVd']"  # XPath for scrolling additional search results
    get_search_url = "https://www.google.se/search?q="  # Base URL for search results

    limit = limit+10
    print(f"Limit set to: {limit}")
    
    # Function to determine if pagination is available on the search results page
    def search_pagination(source):
        """
        Checks if pagination is available on the search results page.

        Args:
            source (str): The HTML source of the search results page.

        Returns:
            bool: True if pagination is available, False otherwise.
        """
        soup = BeautifulSoup(source, features="lxml")
        return bool(soup.find("span", class_=["SJajHc", "NVbCr"]))

    # Function to scrape search results from the current page
    def get_search_results(driver, page):
        """
        Extracts search results from the current page.

        Args:
            driver (Driver): The Selenium WebDriver instance.
            page (int): The current page number.

        Returns:
            list: A list of search results, each containing the title, description, URL, and metadata.
        """
        results = []
        source = driver.page_source

        # Encode the page source and take a screenshot
        serp_code = scraping.encode_code(source)
        serp_bin = scraping.take_screenshot(driver)
        soup = BeautifulSoup(source, features="lxml")

        # Remove undesired elements from the page
        undesired_classes = ["d4rhi", "Wt5Tfe", "UDZeY fAgajc OTFaAf"]
        for cls in undesired_classes:
            for element in soup.find_all("div", class_=cls):
                element.extract()

        # Extract search results
        for result in soup.find_all("div", class_=["tF2Cxc", "dURPMd"]):
            result_title = ""
            result_description = ""
            result_url = ""

            # Extract the title
            try:
                title_element = result.find("h3", class_=["LC20lb", "MBeuO", "DKV0Md"])
                if title_element:
                    result_title = title_element.text.strip()
            except Exception:
                result_title = "N/A"

            # Extract the description
            try:
                description_element = result.find("div", class_=re.compile("VwiC3b", re.I))
                if description_element:
                    result_description = description_element.text.strip()
            except Exception:
                result_description = "N/A"

            # Extract URL
            try:
                urls = result.find_all("a")
                if urls:
                    url = urls[0].attrs.get('href', "N/A")
                    result_url = url
            except Exception:
                result_url = "N/A"

            # Add the result if URL is valid
            if result_url != "N/A" and result_url.startswith(("http://", "https://")):
                results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

        return results

    # Function to check if CAPTCHA is present on the page
    def check_captcha(driver):
        """
        Checks if a CAPTCHA is present on the page.

        Args:
            driver (Driver): The Selenium WebDriver instance.

        Returns:
            bool: True if CAPTCHA is present, False otherwise.
        """
        source = driver.page_source
        return captcha in source

    # Function to remove duplicate search results based on the URL
    def remove_duplicates(search_results):
        """
        Removes duplicate search results based on the URL.

        Args:
            search_results (list): List of search results to deduplicate.

        Returns:
            list: List of search results with duplicates removed.
        """
        seen_urls = set()
        unique_results = []

        for result in search_results:
            url = result[2]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results
    
    # Function to initialize a new WebDriver with optional proxy
    def init_driver(proxy=None, attempt=0):
        ua = UserAgent(platforms='pc', browsers='chrome')
        user_agent = ua.random
        
        print("=" * 50)
        print(f"ATTEMPT {attempt+1}/{max_retries}")
        print(f"Using User-Agent: {user_agent}")
        
        driver_options = {
            "browser": "chrome",
            "wire": True,
            "uc": True,
            "headless2": headless,
            "incognito": False,
            "agent": user_agent,
            "do_not_track": True,
            "undetectable": True,
            "extension_dir": ext_path,
            "locale_code": "sv-SE",
            "no_sandbox": True            
        }
        
        if proxy:
            driver_options["proxy"] = proxy
            print(f"Using proxy: {proxy}")
            print(f"Proxy usage: {len(used_proxies)}/{len(all_proxies)} proxies used so far")
        else:
            print("No proxy being used for this attempt")
            
        print("=" * 50)
        return Driver(**driver_options)
    
    # Function to perform the search and get results
    def perform_search(driver, search_query):
        try:
            results_number = 0
            page = 1
            
            print("Setting up browser...")
            driver.set_page_load_timeout(20)
            driver.implicitly_wait(30)
            
            print(f"Navigating to Google search page...")
            driver.get(search_url)
            time.sleep(random.randint(1, 2))
            
            if check_captcha(driver):
                print("⚠️ CAPTCHA detected on the initial page")
                return -1
            else:
                print("✓ Initial page loaded without CAPTCHA")
                
            # Enter search query and submit
            print(f"Entering search query: '{search_query}'")
            search_box_element = driver.find_element(By.NAME, search_box)
            search_box_element.send_keys(search_query)
            search_box_element.send_keys(Keys.RETURN)
            print("Search query submitted")
            time.sleep(random.randint(1, 2))
            
            # Check for CAPTCHA after search
            if check_captcha(driver):
                print("⚠️ CAPTCHA detected after search submission")
                return -1
            else:
                print("✓ Search results page loaded without CAPTCHA")
                
            # Get initial search results
            print("Extracting search results from first page...")
            initial_results = get_search_results(driver, page)
            initial_results = remove_duplicates(initial_results)
            results_number = len(initial_results)
            
            print(f"📊 Initial results: {results_number} items found for '{search_query}'")
            
            # If no results, return empty list to trigger retry
            if results_number == 0:
                print("⚠️ No initial results found - will retry with different proxy")
                return []
                
            # If we have enough results, return them
            if results_number >= limit:
                return initial_results[:limit]
                
            # Otherwise, continue searching through pagination
            all_results = initial_results
            
            # Check if pagination is available
            pagination_available = search_pagination(driver.page_source)
            
            if pagination_available:
                print("Pagination found, gathering more results...")
                continue_scraping = True
                
                # Navigate through pages
                while results_number < limit and page < (limit / 10) and continue_scraping:
                    if check_captcha(driver):
                        print("CAPTCHA detected during pagination")
                        return -1
                        
                    time.sleep(random.randint(1, 2))
                    page += 1
                    page_label = f"Page {page}"
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    try:
                        next_button = driver.find_element(By.XPATH, next_page_xpath.format(page_label))
                        next_button.click()
                        page_results = get_search_results(driver, page)
                        all_results += page_results
                        all_results = remove_duplicates(all_results)
                        results_number = len(all_results)
                    except Exception as e:
                        print(f"Error navigating to next page: {e}")
                        continue_scraping = False
                
                return all_results[:limit] if len(all_results) > 0 else -1
            else:
                print("No pagination found, using URL parameters...")
                start = 0
                formatted_query = search_query.lower().replace(" ", "+")
                all_results = initial_results
                continue_scraping = True
                
                # Use URL parameters to get more results
                while results_number < limit and start <= limit and continue_scraping:
                    if check_captcha(driver):
                        print("CAPTCHA detected during URL parameter search")
                        return -1
                        
                    try:
                        start += 10
                        page += 1
                        edit_search_url = f"{get_search_url}{formatted_query}&start={start}"
                        print(f"Fetching: {edit_search_url}")
                        driver.get(edit_search_url)
                        time.sleep(random.randint(1, 2))
                        
                        page_results = get_search_results(driver, page)
                        
                        if page_results:
                            all_results += page_results
                            all_results = remove_duplicates(all_results)
                            results_number = len(all_results)
                        else:
                            print("No more results found")
                            continue_scraping = False
                    except Exception as e:
                        print(f"Error during URL parameter search: {e}")
                        continue_scraping = False
                
                return all_results[:limit] if len(all_results) > 0 else -1
        
        except Exception as e:
            print(f"Exception in perform_search: {e}")
            return -1
    
    # Main loop with retries for proxies
    while retry_count < max_retries:
        try:
            # Always get a new proxy after the first attempt
            proxy = get_proxy() if retry_count > 0 else None
            
            # Initialize the driver with optional proxy and show attempt number
            driver = init_driver(proxy, retry_count)
            
            # Perform the search
            search_results = perform_search(driver, query)
            
            # If we got valid results, we're done
            if isinstance(search_results, list) and len(search_results) > 0:
                print("\n" + "=" * 50)
                print(f"SUCCESS! Found {len(search_results)} results")
                print("=" * 50 + "\n")
                break
                
            # If no results or CAPTCHA, retry with a new proxy
            retry_count += 1
            print("\n" + "!" * 50)
            print(f"Attempt {retry_count} failed. " + 
                  ("CAPTCHA detected" if search_results == -1 else "No results found"))
            
            if retry_count < max_retries:
                print(f"Retrying with a new proxy (attempt {retry_count+1}/{max_retries} coming up)")
            else:
                print("Maximum retry attempts reached. Giving up.")
            print("!" * 50 + "\n")
            
        except Exception as e:
            print(f"\nException in main loop: {e}")
            retry_count += 1
            
            if retry_count < max_retries:
                print(f"Retrying after error (attempt {retry_count+1}/{max_retries} coming up)")
            else:
                print("Maximum retry attempts reached. Giving up.")
        finally:
            # Clean up the driver
            if driver:
                try:
                    driver.quit()
                    print("WebDriver successfully closed")
                except Exception as e:
                    print(f"Error closing WebDriver: {e}")
                    pass
                    
    return search_results