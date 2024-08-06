"""
This template outlines the steps required to add a custom scraper for the RAT software. The current implementation assumes that the target search services provide search forms. However, other types of search systems can be integrated by adapting the procedure accordingly. Selenium is used as the basis for scraping.

For scraping search results, you need to:
1. Define the search service and create a corresponding scraper Python file.
2. Implement appropriate functions that are consistent across all search engines, though their implementations may vary.

The final output should include search results with the following fields:
- `result_title`: The title of the search result.
- `result_description`: The description of the search result.
- `result_url`: The URL of the search result.
- `serp_code`: The HTML source of the search result page.
- `serp_bin`: A screenshot of the search result page.
- `page`: The page number of the search results.

Common functions in a scraper include:
- `run(query, limit, scraping)`: The main function for all scrapers with parameters:
  - `query` (str): The search query.
  - `limit` (int): The maximum number of results to retrieve.
  - `scraping` (Scraping): An object with functions for scraping.
- `get_search_results(driver, page)`: Retrieves search results from the current page.
- `check_captcha(driver)`: Checks for CAPTCHA to determine if scraping should be aborted.

The following code outlines the standard variables and functionality required to scrape a search engine, which can be customized as needed.
"""

from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Main function to scrape search results from the KatalogPlus DE Articles search engine.

    Args:
        query (str): The search query.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class for encoding page source and taking screenshots.
        headless (int): Flag indicating whether to run the scraper in headless mode (0 for False, 1 for True).

    Returns:
        list: List of search results, each represented as a list containing:
              - title (str): The title of the search result.
              - description (str): The description of the search result.
              - url (str): The URL of the search result.
              - serp_code (str): Encoded HTML source of the search result page.
              - serp_bin (bytes): Screenshot of the search result page.
              - page (int): The page number of the search results.
              Returns -1 if CAPTCHA is detected or an error occurs.
    """
    try:
        # Define constants for scraping the KatalogPlus search engine
        search_url = "https://katalogplus.sub.uni-hamburg.de/vufind/Search2/"  # URL of the search engine
        search_box = "lookfor"  # Class name of the search box (input field for searches)
        captcha_marker = "g-recaptcha"  # Marker for CAPTCHA detection
        next_page_xpath = "//a[@class='page-next']"  # XPath to locate the "Next" button for pagination
        results_number = 0  # Initialize results count
        page = 1  # Initialize page number
        search_results = []  # List to store search results

        def get_search_results(driver, page):
            """
            Extracts and parses search results from the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of extracted search results, each containing:
                      - title (str): The title of the search result.
                      - description (str): The description of the search result.
                      - url (str): The URL of the search result.
                      - serp_code (str): Encoded HTML source of the search result page.
                      - serp_bin (bytes): Screenshot of the search result page.
                      - page (int): The page number of the search results.
            """
            results = []  # List to store search results
            source = driver.page_source  # Get the page source

            # Encode the page source and capture a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")  # Parse the page source with BeautifulSoup

            # Extract search results from the parsed HTML
            for result in soup.find_all("div", class_=["result-body"]):
                result_title = "N/A"
                result_description = "N/A"
                result_url = "N/A"

                # Extract the title of the search result
                try:
                    title_element = result.find("a", class_=["title", "getFull"])
                    if title_element:
                        result_title = title_element.text.strip()
                except Exception as e:
                    print(f"Error extracting title: {e}")

                # Extract and clean the description of the search result
                try:
                    description_elements = result.find_all("div")
                    for description in description_elements:
                        text = description.text.strip()
                        result_description += text
                        result_description = result_description.replace(result_title, " ")
                        result_description = result_description.replace("\n", "")
                        result_description = result_description.replace("Veröffentlicht", " Veröffentlicht")
                        result_description = " ".join(result_description.split())
                except Exception as e:
                    print(f"Error extracting description: {e}")

                # Extract the URL of the search result
                try:
                    url_elements = result.find_all("a")
                    for url_element in url_elements:
                        url = url_element.attrs.get('href', "N/A")
                        result_url = f"https://katalogplus.sub.uni-hamburg.de{url}"
                        break
                except Exception as e:
                    print(f"Error extracting URL: {e}")

                # Append the result to the list if the URL is valid
                if result_url != "N/A" and "http" in result_url:
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
            locale_code="de",  # Set locale to German
            no_sandbox=True
        )

        driver.maximize_window()  # Maximize the browser window
        driver.set_page_load_timeout(20)  # Set a timeout for page loading
        driver.implicitly_wait(30)  # Set an implicit wait for elements
        driver.get(search_url)  # Navigate to the search URL
        time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            # Perform the search
            search_box_element = driver.find_element(By.NAME, search_box)
            search_box_element.send_keys(query)
            search_box_element.send_keys(Keys.RETURN)

            time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection

            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            continue_scraping = True  # Flag to control the scraping loop

            # Continue scraping while the number of results is less than the limit
            while results_number < limit and continue_scraping:
                if not check_captcha(driver):
                    time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection
                    page += 1  # Increment page number
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll down to load more results

                    try:
                        next_page_element = driver.find_element(By.XPATH, next_page_xpath)
                        next_page_element.click()  # Click on the "Next" button to go to the next page
                        search_results += get_search_results(driver, page)
                        results_number = len(search_results)
                    except Exception as e:
                        print(f"Error during pagination: {e}")
                        continue_scraping = False  # Stop scraping if pagination fails
                else:
                    print("CAPTCHA detected.")
                    search_results = -1
                    continue_scraping = False

            # Quit the driver if running in headless mode
            if headless == 1:
                driver.quit()
                
            return search_results

        else:
            print("CAPTCHA detected.")
            search_results = -1
            if headless == 1:
                driver.quit()
                
            return search_results

    except Exception as e:
        print(f"Exception occurred: {e}")
        try:
            driver.quit()
        except Exception as quit_exception:
            print(f"Error quitting the driver: {quit_exception}")
        return -1
