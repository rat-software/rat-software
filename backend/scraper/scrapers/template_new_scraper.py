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

The search engine in this template is Ecosia. Change the parameters according to the search engine you want to scrape.
"""

from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Run the scraper.

    Args:
        query (str): The search query.
        limit (int): The maximum number of search results to retrieve.
        scraping: The Scraping object.
        headless (bool): If True, runs the browser in headless mode (without GUI).

    Returns:
        list: List of search results.
    """
    try:
        # URL and selectors for the search engine
        search_url = "https://www.ecosia.org/" #URL for the search engine
        search_box = "q" #Selector for the search box
        captcha = "g-recaptcha" #Selector for CAPTCHA in the page source

        # Initialize variables
        results_number = 0 #Initialize number of search results
        page = -1 #Initialize SERP page number
        search_results = [] #Initialize list of search results
        
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

            # Extract search results using CSS selectors
            for result in soup.find_all("div", class_=["result__body"]):
                result_title = "N/A" #Initialize result title
                result_description = "N/A" #Initialize result description
                result_url = "N/A" #Initialize result URL

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

            # Append only unique results
            for result in search_results:
                url = result[2]
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)

            return unique_results        

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
            locale_code="de"
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(2, 5))

        # Start scraping if no CAPTCHA
        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box) #Find search box
            search.send_keys(query) #Enter search query
            search.send_keys(Keys.RETURN) #Submit search
            time.sleep(random.randint(2, 5)) #Wait for Results

            search_results = get_search_results(driver, page)
            results_number = len(search_results)
            continue_scraping = True #Initialize scraping

            # Loop through pages until limit is reached or CAPTCHA appears
            while results_number < limit and continue_scraping:
                if not check_captcha(driver):
                    time.sleep(random.randint(2, 5))
                    page += 1
                    try:
                        next_page_url = f"https://www.ecosia.org/search?method=index&q={query}&p={page}" #Next page URL
                        print(next_page_url)
                        driver.get(next_page_url)
                        extract_search_results = get_search_results(driver, page)
                        print(f"Results extracted: {len(extract_search_results)}")

                        if extract_search_results:
                            print("Appending results.")
                            search_results += extract_search_results
                            search_results = remove_duplicates(search_results)
                            results_number = len(search_results)
                        else:
                            continue_scraping = False
                            search_results = -1
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
