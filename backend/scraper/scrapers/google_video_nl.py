from scrapers.requirements import *
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Scrapes video search results from Google Netherlands based on the provided query.

    Args:
        query (str): The search query to be used in Google video search.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class for additional operations such as encoding and screenshots.
        headless (bool): If True, runs the browser in headless mode (without GUI).

    Returns:
        list: A list of search results where each result contains:
              - title: The title of the search result.
              - description: A brief description of the search result.
              - url: The URL of the search result.
              - serp_code: Encoded page source for the search results.
              - serp_bin: Screenshot of the search results page.
              - page: The page number from which the result was retrieved.
              Returns -1 if CAPTCHA is detected or an error occurs during the scraping process.
    """
    try:
        # Define constants and initial variables
        search_url = "https://www.google.nl/search?hl=nl&gl=NL&tbm=vid&prmd=ivnbz&source=lnt&uule=w+CAIQICILTmV0aGVybGFuZHM="
        captcha_marker = "g-recaptcha"  # Marker for CAPTCHA detection
        results_number = 0
        page = 1
        search_results = []

        def search_pagination(source):
            """
            Checks if pagination controls are present on the search results page.

            Args:
                source (str): The HTML source of the search results page.

            Returns:
                bool: True if pagination controls are found, False otherwise.
            """
            soup = BeautifulSoup(source, features="lxml")
            return bool(soup.find("span", class_=["SJajHc", "NVbCr"]))

        def get_search_results(driver, page):
            """
            Extracts and parses search results from the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of extracted search results, where each result includes title, description, URL, 
                      and metadata such as encoded page source and screenshot.
            """
            results = []
            source = driver.page_source

            # Encode the page source and capture a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, features="lxml")

            for result in soup.find_all("div", class_=["MjjYud"]):
                result_title = ""
                result_description = ""
                result_url = ""

                # Extract the title of the search result
                try:
                    title_element = result.find("h3", class_=["LC20lb", "MBeuO", "DKV0Md"])
                    if title_element:
                        result_title = title_element.text.strip()
                except Exception as e:
                    print(f"Error extracting title: {e}")
                    result_title = "N/A"

                # Extract the description of the search result
                try:
                    description_element = result.find("div", class_=["fzUZNc"])
                    if description_element:
                        result_description = description_element.text.strip()
                except Exception as e:
                    print(f"Error extracting description: {e}")
                    result_description = "N/A"

                # Extract the URL of the search result
                try:
                    url_element = result.find("a")
                    if url_element:
                        url = url_element.attrs.get('href', "N/A")
                        if "bing." in url:
                            url = scraping.get_real_url(url)
                        result_url = url
                except Exception as e:
                    print(f"Error extracting URL: {e}")
                    result_url = "N/A"

                # Append the result if the URL is valid
                if result_url != "N/A" and "http" in result_url and "/search?" not in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return results

        def check_captcha(driver):
            """
            Checks if CAPTCHA is present on the page.

            Args:
                driver (Driver): The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, False otherwise.
            """
            source = driver.page_source
            return captcha_marker in source

        # Initialize Selenium WebDriver
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,  # Run browser in headless mode if specified
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="nl",  # Set locale to Dutch
            no_sandbox=True
        )

        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        time.sleep(random.randint(2, 5))  # Random delay to prevent detection

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            start = 0

            query = query.lower().replace(" ", "+")
            search_query = f"&q={query}&start={start}"
            search_result_query = search_url + search_query
            
            driver.get(search_result_query)
            time.sleep(random.randint(2, 5))  # Random delay to prevent detection
            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            continue_scraping = True

            while results_number < limit and continue_scraping:
                if not check_captcha(driver):
                    try:
                        time.sleep(random.randint(2, 5))  # Random delay to prevent detection
                        page += 1
                        start += 10
                        search_query = f"&q={query}&start={start}"
                        search_result_query = search_url + search_query
                        driver.get(search_result_query)
                        search_results += get_search_results(driver, page)
                        results_number = len(search_results)
                    except Exception as e:
                        print(f"Error during scraping: {e}")
                        continue_scraping = False
                        search_results = -1
                else:
                    print("CAPTCHA detected.")
                    search_results = -1
                    continue_scraping = False

            try:
                driver.quit()
            except Exception as e:
                print(f"Error quitting the driver: {e}")

            return search_results

    except Exception as e:
        print(f"Exception occurred: {e}")
        try:
            driver.quit()
        except Exception as e:
            print(f"Error quitting the driver during exception handling: {e}")
        return -1
