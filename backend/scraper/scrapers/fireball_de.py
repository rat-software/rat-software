from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Scrapes search results from KatalogPlus DE Articles.

    Args:
        query (str): The search query.
        limit (int): The maximum number of search results to retrieve.
        scraping: The Scraping object with functions for encoding and screenshots.
        headless (bool): Whether to run the scraper in headless mode.

    Returns:
        list: A list of search results, or -1 if CAPTCHA is detected or an error occurs.
    """
    try:
        # Define scraping parameters
        search_url = f"https://fireball.de/search?q={query}"  # URL for the search engine
        search_box_name = "q"  # Name attribute for the search input box
        captcha_indicator = "g-recaptcha"  # Indicator for CAPTCHA
        results_number = 0  # Number of results found
        page = 1  # Current SERP page number
        search_results = []  # List to store search results

        def get_search_results(driver, page):
            """
            Extract search results from the current page.

            Args:
                driver: Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: List of search results from the current page.
            """
            results = []  # Temporary list to store results
            source = driver.page_source  # Get the page source

            # Encode source and take a screenshot for analysis
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            # Parse the source using BeautifulSoup
            soup = BeautifulSoup(source, "lxml")

            # Extract search results
            for result in soup.find_all("div", class_=["search-result search-result-web"]):
                result_title = "N/A"
                result_description = "N/A"
                result_url = "N/A"

                # Extract title
                try:
                    title_elem = result.find("a", class_=["search-result-title"])
                    result_title = title_elem.text.strip() if title_elem else "N/A"
                except:
                    pass

                # Extract description
                try:
                    description_elems = result.find_all("div", class_=["search-result-text"])
                    result_description = " ".join([desc.text.strip() for desc in description_elems])
                    result_description = result_description.replace(result_title, "").strip()
                except:
                    pass

                # Extract URL
                try:
                    url_elem = result.find("a", class_=["search-result-url"])
                    result_url = url_elem.attrs['href'] if url_elem else "N/A"
                except:
                    pass

                # Append result if within limit
                if len(results) < limit:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return results

        def check_captcha(driver):
            """
            Check if CAPTCHA is present on the page.

            Args:
                driver: Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, False otherwise.
            """
            source = driver.page_source
            return captcha_indicator in source

        # Initialize Selenium WebDriver
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="de"
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(2, 5))  # Random sleep to avoid detection

        # Start scraping if no CAPTCHA
        if not check_captcha(driver):
            search_box = driver.find_element(By.NAME, search_box_name)
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.randint(2, 5))  # Random sleep to avoid detection

            search_results = get_search_results(driver, page)
            driver.quit()
            return search_results
        else:
            driver.quit()
            return -1  # CAPTCHA detected

    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            driver.quit()
        except:
            pass
        return -1  # Error occurred
