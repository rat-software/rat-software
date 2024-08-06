from scrapers.requirements import *
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Scrape video search results from Google Sweden based on the provided query.

    Args:
        query (str): The search query to be used in Google video search.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class for encoding page source and taking screenshots.
        headless (bool): If True, runs the browser in headless mode (without GUI).

    Returns:
        list: A list of search results where each result is represented as a list containing:
              - title (str): The title of the search result.
              - description (str): A brief description of the search result.
              - url (str): The URL of the search result.
              - serp_code (str): Encoded page source for the search results.
              - serp_bin (bytes): Screenshot of the search results page.
              - page (int): The page number from which the result was retrieved.
              Returns -1 if CAPTCHA is detected or an error occurs during scraping.
    """
    try:
        # Define constants for scraping Google search results
        search_url = "https://www.google.nl/search?hl=sv&gl=SE&tbm=vid&prmd=ivnbz&source=lnt&uule=ww+CAIQICIMU3dlZGVuLCBMdW5k"
        captcha_marker = "g-recaptcha"  # Marker for CAPTCHA detection
        results_number = 0  # Initialize count of results retrieved
        page = 1  # Initialize SERP page number
        search_results = []  # List to store search results

        # Function to determine if pagination is available on the search results page
        def search_pagination(source):
            """
            Checks for the presence of pagination controls in the search results page.

            Args:
                source (str): The HTML source of the search results page.

            Returns:
                bool: True if pagination controls are present, False otherwise.
            """
            soup = BeautifulSoup(source, features="lxml")
            return bool(soup.find("span", class_=["SJajHc", "NVbCr"]))

        # Function to extract search results from the current page
        def get_search_results(driver, page):
            """
            Extracts and parses search results from the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of extracted search results, where each result includes:
                      - title (str): The title of the search result.
                      - description (str): The description of the search result.
                      - url (str): The URL of the search result.
                      - serp_code (str): Encoded page source for the search results.
                      - serp_bin (bytes): Screenshot of the search results page.
                      - page (int): The page number from which the result was retrieved.
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

        # Function to check for CAPTCHA presence
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

        # Initialize Selenium WebDriver with specified options
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
            locale_code="sv",  # Set locale to Swedish
            no_sandbox=True
        )

        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            start = 0
            results_number = 0

            # Format the query for URL
            query_formatted = query.lower().replace(" ", "+")
            search_query = f"&q={query_formatted}&start={start}"
            search_result_query = search_url + search_query
            
            driver.get(search_result_query)
            time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection
            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            while results_number < limit:
                if not check_captcha(driver):
                    try:
                        time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection
                        page += 1
                        start += 10
                        search_query = f"&q={query_formatted}&start={start}"
                        search_result_query = search_url + search_query
                        driver.get(search_result_query)
                        search_results += get_search_results(driver, page)
                        results_number = len(search_results)
                    except Exception as e:
                        print(f"Error during scraping: {e}")
                        search_results = -1
                        break
                else:
                    print("CAPTCHA detected.")
                    search_results = -1
                    break

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
