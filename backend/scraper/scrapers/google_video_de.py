from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
import re
import time
import random

def run(query, limit, scraping, headless):
    """
    Scrape Google DE video search results based on the provided query.

    Args:
        query (str): The search query to use for Google DE video search.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class used for encoding page source and taking screenshots.
        headless (bool): If True, run the browser in headless mode (without GUI).

    Returns:
        list: A list of search results, where each result contains the title, description, URL, 
              and metadata (encoded page source and screenshot binary). Returns -1 if CAPTCHA is detected 
              or if an error occurs during scraping.
    """
    try:
        # Define constants for scraping Google DE video search
        search_url = "https://www.google.de/search?hl=de&gl=DE&tbm=vid&prmd=ivnbz&source=lnt&uule=w+CAIQICIHR2VybWFueQ=="  # URL for Google video search
        search_box_name = "search_query"  # Name attribute of the search input box
        captcha_marker = "g-recaptcha"  # Indicator for CAPTCHA presence
        next_page_xpath = "//a[@aria-label='{}']"  # XPath template for the "next" button
        next_scroll_xpath = "//span[@class='RVQdVd']"  # XPath for scrolling additional search results

        # Initialize variables
        results_number = 0
        page = 1
        search_results = []

        # Function to check for pagination
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

        # Function to extract search results from the page
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

            # Extract search results from the page
            for result in soup.find_all("div", class_=["MjjYud"]):
                result_title = ""
                result_description = ""
                result_url = ""

                try:
                    title_element = result.find("h3", class_=["LC20lb", "MBeuO", "DKV0Md"])
                    if title_element:
                        result_title = title_element.text.strip()
                except Exception:
                    result_title = "N/A"

                try:
                    description_element = result.find("div", class_=["fzUZNc"])
                    if description_element:
                        result_description = description_element.text.strip()
                except Exception:
                    result_description = "N/A"

                try:
                    url_element = result.find("a")
                    if url_element:
                        url = url_element.attrs.get('href', "N/A")
                        if "bing." in url:
                            url = scraping.get_real_url(url)
                        result_url = url
                except Exception:
                    result_url = "N/A"

                if result_url != "N/A" and "http" in result_url and "/search?" not in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return results

        # Function to check if a CAPTCHA is present on the page
        def check_captcha(driver):
            """
            Checks if a CAPTCHA is present on the page.

            Args:
                driver (Driver): The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is present, False otherwise.
            """
            source = driver.page_source
            return captcha_marker in source

        # Initialize Selenium WebDriver
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,  # Run in headless mode if specified
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="de",  # Set locale to German
            no_sandbox=True
        )

        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        time.sleep(random.randint(2, 5))  # Random sleep to avoid quick automatic blocking

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            start = 0
            page = 1
            query = query.lower().replace(" ", "+")
            search_query = f"&q={query}&start={start}"
            search_result_query = search_url + search_query
            
            driver.get(search_result_query)
            time.sleep(random.randint(2, 5))  # Random sleep to avoid detection

            # Get initial search results
            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            continue_scraping = True

            # Continue scraping if results number is less than the limit
            while results_number < limit and continue_scraping:
                if not check_captcha(driver):
                    try:
                        time.sleep(random.randint(2, 5))  # Random sleep to avoid detection
                        page += 1
                        start += 10
                        search_query = f"&q={query}&start={start}"
                        search_result_query = search_url + search_query
                        driver.get(search_result_query)
                        search_results += get_search_results(driver, page)
                        results_number = len(search_results)
                    except Exception as e:
                        print(f"Error occurred during scraping: {e}")
                        continue_scraping = False
                        search_results = -1
                else:
                    continue_scraping = False
                    search_results = -1

            try:
                driver.quit()
            except Exception as e:
                print(f"Error occurred while quitting driver: {e}")
            
            return search_results

    except Exception as e:
        print(f"Exception occurred: {e}")
        try:
            driver.quit()
        except:
            pass
        return -1
