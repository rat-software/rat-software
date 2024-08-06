from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Run the Ecosia EN scraper.

    Args:
        query (str): The search query.
        limit (int): The maximum number of search results to retrieve.
        scraping: The Scraping object.
        headless (int): Flag indicating whether to run the scraper in headless mode.

    Returns:
        list: List of search results.
    """
    try:
        # URL and selectors for the search engine
        search_url = "https://www.ecosia.org/"
        search_box = "q"
        captcha = "g-recaptcha"

        # Initialize variables
        results_number = 0
        page = 0
        search_results = []
        limit += 10  # to account for extra results due to possible duplication

        # Custom function to scrape search results
        def get_search_results(driver, page):
            """
            Retrieve search results from the current page.

            Args:
                driver: Selenium WebDriver instance.
                page (int): Current SERP page.

            Returns:
                list: List of search results from the current page.
            """
            temp_search_results = []

            # Get page source and encode it
            source = driver.page_source
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(source, features="lxml")

            # Extract search results
            for result in soup.find_all("div", class_=["result__body"]):
                result_title = "N/A"
                result_description = "N/A"
                result_url = "N/A"

                try:
                    title_elem = result.find("div", class_=["result__title"])
                    if title_elem:
                        result_title = title_elem.text.strip()
                except:
                    pass

                try:
                    description_elem = result.find("div", class_=["result__description"])
                    if description_elem:
                        result_description = description_elem.text.strip()
                except:
                    pass

                try:
                    url_elem = result.find("a")
                    if url_elem:
                        url = url_elem.attrs['href']
                        if "bing." in url:
                            url = scraping.get_real_url(url)
                        result_url = url
                except:
                    pass

                if result_url != "N/A":
                    temp_search_results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return temp_search_results

        # Custom function to check if CAPTCHA is present
        def check_captcha(driver):
            """
            Check if CAPTCHA is present on the page.

            Args:
                driver: Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is present, False otherwise.
            """
            source = driver.page_source
            return captcha in source

        # Initialize Selenium driver
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
            locale_code="en"
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(2, 5))

        # Start scraping if no CAPTCHA
        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(random.randint(2, 5))

            search_results = get_search_results(driver, page)
            results_number = len(search_results)
            continue_scraping = True

            # Loop through pages until limit is reached or CAPTCHA appears
            while results_number < limit and continue_scraping:
                if not check_captcha(driver):
                    time.sleep(random.randint(2, 5))
                    page += 1
                    try:
                        next_page_url = f"https://www.ecosia.org/search?method=index&q={query}&p={page}"
                        driver.get(next_page_url)
                        search_results += get_search_results(driver, page)
                        results_number = len(search_results)
                    except Exception as e:
                        print(f"Failed to get next page: {e}")
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

    except Exception as e:
        print(f"Exception occurred: {e}")
        try:
            driver.quit()
        except:
            pass
        return -1
