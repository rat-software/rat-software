"""
This template outlines the necessary steps to create a custom scraper for the RAT software. It is designed for search services that provide search forms but can be adapted for other types of search systems. Selenium is used as the core tool for scraping.

### Overview:
1. Define the target search service and create a corresponding scraper Python file.
2. Implement necessary functions that are consistent across all scrapers, though their specifics may vary.

### Output:
The scraper should return results with the following fields:
- `result_title`: Title of the search result snippet.
- `result_description`: Description in the search result snippet.
- `result_url`: URL of the search result.
- `serp_code`: HTML source of the search results page for further analysis.
- `serp_bin`: Screenshot of the search results page, if needed for analysis.
- `page`: Page number of the search results.

### Key Functions:
- `run(query, limit, scraping, headless)`: Main function for initiating the scraping process.
- `get_search_results(driver, page)`: Retrieves search results from the current page.
- `check_captcha(driver)`: Helper function to detect CAPTCHA and determine if scraping should continue.

This code provides a standard approach to scraping search engines but can be customized based on specific requirements.
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
    Main function to scrape search results from the KatalogPlus DE Books search engine.

    Args:
        query (str): The search query to use.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class for encoding and screenshot functions.
        headless (int): Flag indicating whether to run the browser in headless mode (1 for True, 0 for False).

    Returns:
        list: A list of search results, each represented as a list containing:
              - result_title (str): Title of the search result.
              - result_description (str): Description of the search result.
              - result_url (str): URL of the search result.
              - serp_code (str): Encoded HTML source of the search result page.
              - serp_bin (bytes): Screenshot of the search result page.
              - page (int): Page number of the search results.
              Returns -1 if CAPTCHA is detected or an error occurs.
    """
    try:
        # Define constants for the scraping process
        search_url = "https://katalogplus.sub.uni-hamburg.de/vufind/Search/"  # URL of the search engine
        search_box = "lookfor"  # Class name of the search box (input field for searches)
        captcha_marker = "g-recaptcha"  # Marker for CAPTCHA detection
        next_page_xpath = "//a[@class='page-next']"  # XPath to find the "Next" button for pagination
        results_number = 0  # Initialize the count of results retrieved
        page = 1  # Initialize the page number
        search_results = []  # List to store the search results

        def get_search_results(driver, page):
            """
            Extracts and parses search results from the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of extracted search results, each containing:
                      - result_title (str): Title of the search result.
                      - result_description (str): Description of the search result.
                      - result_url (str): URL of the search result.
                      - serp_code (str): Encoded HTML source of the search result page.
                      - serp_bin (bytes): Screenshot of the search result page.
                      - page (int): The page number of the search results.
            """
            results = []  # Temporary list to store search results
            source = driver.page_source  # Get the page source

            # Encode the page source and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")  # Parse the page source

            # Extract search results from the parsed HTML
            for result in soup.find_all("div", class_=["result-body"]):
                result_title = "N/A"
                result_description = "N/A"
                result_url = "N/A"

                try:
                    title_element = result.find("a", class_=["title", "getFull"])
                    if title_element:
                        result_title = title_element.text.strip()
                except Exception as e:
                    print(f"Error extracting title: {e}")

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

                try:
                    url_elements = result.find_all("a")
                    for url_element in url_elements:
                        url = url_element.attrs.get('href', "N/A")
                        result_url = f"https://katalogplus.sub.uni-hamburg.de{url}"
                        break
                except Exception as e:
                    print(f"Error extracting URL: {e}")

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

        if not check_captcha(driver):
            # Perform the search
            search_box_element = driver.find_element(By.NAME, search_box)
            search_box_element.send_keys(query)
            search_box_element.send_keys(Keys.RETURN)

            time.sleep(random.randint(2, 5))  # Random delay to reduce risk of detection

            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            continue_scraping = True  # Flag to control the scraping loop

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
