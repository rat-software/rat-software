"""
This script provides a template for creating a custom web scraper for the RAT software using Selenium. The scraper is designed to work with search engines that offer search forms but can be adapted for other types of search systems. 

The scraper extracts the following information:
- `result_title`: The title of each search result.
- `result_description`: The description associated with each search result.
- `result_url`: The URL of each search result.
- `serp_code`: The HTML source code of the search result page.
- `serp_bin`: A screenshot of the search result page.
- `page`: The page number of search results, useful for pagination or scrolling-based systems.

Functions included in the scraper:
- `run(query, limit, scraping, headless)`: The main function to perform scraping with given parameters.
- `get_search_results(driver, page)`: Helper function to extract search results from the page.
- `check_captcha(driver)`: Helper function to determine if CAPTCHA is present.

The scraper configuration and functions can be customized to fit different search engines.
"""

from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import random
import time

def run(query, limit, scraping, headless):
    """
    Executes the scraping process for the specified search engine.

    Args:
        query (str): The search query to be used.
        limit (int): The maximum number of results to retrieve.
        scraping: The Scraping object that provides utility functions.
        headless (bool): Whether to run the browser in headless mode (True or False).

    Returns:
        list: A list of search results, where each result includes title, description, URL, SERP code, screenshot, and page number.
        int: Returns -1 if scraping failed or CAPTCHA is encountered.
    """
    try:
        # Define constants and variables for scraping
        search_url = "https://www.mojeek.de/"  # URL of the search engine
        search_box = "q"  # Name attribute of the search box
        captcha = "g-recaptcha"  # Indicator for CAPTCHA in the page source
        next_page = "Next"  # Link text for "next page" button or navigation
        results_number = 0  # Initialize count of results retrieved
        page = 1  # Initialize current page number
        search_results = []  # List to store search results

        def get_search_results(driver, page):
            """
            Extracts search results from the current page.

            Args:
                driver: The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of search results, each containing title, description, URL, SERP code, screenshot, and page number.
            """
            counter = 0  # Counter to limit the number of search results
            results = []  # Temporary list to store search results

            # Get the HTML source of the current page
            source = driver.page_source

            # Encode the source code and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            # Parse the HTML source with BeautifulSoup
            soup = BeautifulSoup(source, "lxml")

            # Extract search results
            for outer in soup.find_all("ul", class_=["results-standard"]):
                for result in outer.find_all("li"):
                    result_title = "N/A"
                    result_description = "N/A"
                    result_url = "N/A"

                    # Extract the title
                    try:
                        title_element = result.find("a", class_=["title"])
                        if title_element:
                            result_title = title_element.text.strip()
                    except Exception as e:
                        result_title = "N/A"

                    # Extract the description
                    try:
                        description_elements = result.find_all("p", class_=["s"])
                        result_description = " ".join(desc.text.strip() for desc in description_elements)
                        result_description = " ".join(result_description.split())
                    except Exception as e:
                        result_description = "N/A"

                    # Extract the URL
                    try:
                        url_elements = result.find_all("a", class_=["title"])
                        if url_elements:
                            result_url = url_elements[0].attrs['href']
                            # Adjust URL if relative
                            if not result_url.startswith('http'):
                                result_url = search_url + result_url
                        else:
                            result_url = "N/A"
                    except Exception as e:
                        result_url = "N/A"

                    # Append the result if within the limit
                    if counter < limit + 2:
                        results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
                        counter += 1

            return results

        def check_captcha(driver):
            """
            Checks if CAPTCHA is present on the page.

            Args:
                driver: The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, otherwise False.
            """
            source = driver.page_source
            return captcha in source

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
            locale_code="de",
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(2, 5))  # Random delay to avoid quick blocking

        if not check_captcha(driver):
            # Perform the search
            search_box_element = driver.find_element(By.NAME, search_box)
            search_box_element.send_keys(query)
            search_box_element.send_keys(Keys.RETURN)
            time.sleep(random.randint(2, 5))  # Random delay to avoid quick blocking

            # Retrieve search results from the first page
            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            if results_number > 0:
                continue_scraping = True  # Flag to continue or stop scraping

                # Scrape subsequent pages if results are below the limit
                while results_number < limit and continue_scraping:
                    if not check_captcha(driver):
                        time.sleep(random.randint(2, 5))  # Random delay
                        page += 1
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll to load more results
                        try:
                            next_button = driver.find_element(By.LINK_TEXT, next_page)
                            next_button.click()
                            search_results += get_search_results(driver, page)
                            results_number = len(search_results)
                        except Exception:
                            continue_scraping = False
                    else:
                        continue_scraping = False
                        search_results = -1

                driver.quit()
                return search_results
            else:
                search_results = -1
                driver.quit()
                return search_results
        else:
            search_results = -1
            driver.quit()
            return search_results

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Scraping failed")
        try:
            driver.quit()
        except Exception as quit_error:
            print(f"Error during driver quit: {str(quit_error)}")
        return -1
    finally:
        try:
            driver.quit()
        except Exception as final_error:
            print(f"Final cleanup error: {str(final_error)}")
