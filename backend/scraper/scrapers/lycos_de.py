"""
This template provides a framework for creating a custom scraper for the RAT software. This scraper is designed to work with search services that offer search forms. For other types of search systems, modifications to this template may be necessary. Selenium is utilized as the primary tool for web scraping.

The scraper should be capable of returning the following fields:
- `result_title`: The title of the search result snippet.
- `result_description`: The description in the snippet of the result.
- `result_url`: The URL of the search result.
- `serp_code`: The HTML source code of the search result page, useful for further analysis.
- `serp_bin`: A screenshot of the search result page, if needed for additional analysis.
- `page`: The page number of search results, useful for paginated results or scrolling-based systems.

A typical scraper consists of the following functions:
- `run(query, limit, scraping, headless)`: The main function to execute the scraper with the given parameters.
- `get_search_results(driver, page)`: A helper function to retrieve search results from the given page.
- `check_captcha(driver)`: A helper function to check for CAPTCHA or similar blocks and handle them appropriately.

The variables and functionality described here can be adapted according to the specific search engine being scraped.
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
        scraping: The Scraping object that provides additional utility functions.
        headless (bool): Whether to run the browser in headless mode (True or False).

    Returns:
        list: A list of search results, where each result is represented as a list containing title, description, URL, SERP code, screenshot, and page number.
        int: Returns -1 if scraping failed or CAPTCHA is encountered.
    """
    try:
        # Define constants for scraping the search engine
        search_url = "https://www.lycos.de/"  # URL of the search engine
        search_box = "q"  # Name attribute of the search box
        captcha = "g-recaptcha"  # Identifier for CAPTCHA in the page source
        next_page = "//ul[@class='pagination']"  # XPath to locate the "next page" element
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
                list: A list of search results, where each result is a list containing title, description, URL, SERP code, screenshot, and page number.
            """
            counter = 0  # Limits the number of search results

            results = []  # Temporary list to store search results

            source = driver.page_source  # Get the HTML source of the page

            # Encode the page source and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(source, "lxml")

            # Extract search results
            for noAds in soup.find_all("div", class_=["results search-results"]):
                for result in noAds.find_all("li", class_=["result-item"]):
                    url_list = []
                    result_title = "N/A"
                    result_description = "N/A"
                    result_url = "N/A"

                    # Extract the title
                    try:
                        title_element = result.find("h2", class_=["result-title"])
                        result_title = title_element.text.strip() if title_element else "N/A"
                    except Exception:
                        result_title = "N/A"

                    # Extract the description
                    try:
                        description_elements = result.find_all("span", class_=["result-description"])
                        result_description = " ".join(desc.text.strip() for desc in description_elements)
                        result_description = result_description.replace(result_title, " ").strip()
                    except Exception:
                        result_description = "N/A"

                    # Extract the URL
                    try:
                        url_elements = result.find_all("a")
                        if url_elements:
                            result_url = url_elements[0].attrs['href']
                            result_url = f"https://www.lycos.de{result_url}"  # Adjust URL if relative
                        else:
                            result_url = "N/A"
                    except Exception:
                        result_url = "N/A"

                    # Append result to the list if within the limit
                    if counter < limit + 2:
                        results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
                        counter += 1

            return results

        def check_captcha(driver):
            """
            Checks if a CAPTCHA is present on the page.

            Args:
                driver: The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, otherwise False.
            """
            source = driver.page_source
            return captcha in source

        # Initialize the Selenium WebDriver
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

            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            if results_number > 0:
                continue_scraping = True

                # Scrape subsequent pages
                while results_number < limit and continue_scraping:
                    if not check_captcha(driver):
                        time.sleep(random.randint(2, 5))  # Random delay
                        page += 1
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll to load more results
                        try:
                            next_button = driver.find_element(By.XPATH, next_page)
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
        except Exception as e:
            print(f"Driver quit error: {str(e)}")
        return -1
    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Final cleanup error: {str(e)}")
