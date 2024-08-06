from scrapers.requirements import *

import csv
import os
import inspect
from pathlib import Path
import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
import re

def run(query, limit, scraping, headless):
    """
    Scrapes Google DE search results based on the provided query.

    Args:
        query (str): The search query to use.
        limit (int): The maximum number of search results to retrieve.
        scraping: An instance of the Scraping class used for encoding and screenshots.
        headless (bool): If True, run the browser in headless mode.

    Returns:
        list: A list of search results where each result is a list containing title, description, URL, and metadata.
    """
    try:
        # Initialize the list for proxies
        proxies = []

        # Get the directory path to locate the proxy file
        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        
        # Load proxies from a CSV file
        with open(os.path.join(currentdir, 'proxies', 'Germany.csv')) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                proxies.append(row)

        # Shuffle the proxies and select one
        random.shuffle(proxies)
        proxy = proxies[0][0] if proxies else None

        # Define URLs and search parameters
        search_url = "https://www.google.de/webhp?hl=de&gl=DE&&uule=w+CAIQICIHR2VybWFueQ=="
        search_box = "q"  # Name attribute of the search box input field
        captcha = "g-recaptcha"  # Identifier for CAPTCHA in the page source
        next_page = "//a[@aria-label='{}']"  # XPath for navigating to the next search results page
        next_scroll = "//span[@class='RVQdVd']"  # XPath for scrolling to the next set of search results
        results_number = 0  # Counter for the number of results retrieved
        page = 1  # Current page number
        search_results = []  # List to store search results
        get_search_url = "https://www.google.de/search?q="
        language = "&hl=de&gl=DE"  # URL parameters for language and location
        print(f"Limit set to: {limit}")

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

        def get_search_results(driver, page):
            """
            Extracts search results from the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of search results with title, description, URL, and metadata.
            """
            results = []
            source = driver.page_source

            # Encode the page source and take a screenshot for analysis
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")

            # Remove undesired elements from the SERP
            undesired_classes = ["d4rhi", "Wt5Tfe", "UDZeY fAgajc OTFaAf"]
            for cls in undesired_classes:
                for element in soup.find_all("div", class_=cls):
                    element.extract()

            # Extract search results from the page
            for result in soup.find_all("div", class_=["tF2Cxc", "dURPMd"]):
                url_list = []
                result_title = ""
                result_description = ""
                result_url = ""

                # Extract title
                try:
                    title = result.find("h3", class_=["LC20lb", "MBeuO", "DKV0Md"])
                    if title:
                        result_title = title.text.strip()
                except Exception:
                    result_title = "N/A"

                # Extract description
                try:
                    description = result.find("div", class_=re.compile("VwiC3b", re.I))
                    if description:
                        result_description = description.text.strip()
                except Exception:
                    result_description = "N/A"

                # Extract URL
                try:
                    urls = result.find_all("a")
                    if urls:
                        url = urls[0].attrs.get('href', "N/A")
                        if "bing." in url:
                            url = scraping.get_real_url(url)
                        url_list.append(url)
                        result_url = url_list[0]
                except Exception:
                    result_url = "N/A"

                # Append result if URL is valid
                if result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return results

        def check_captcha(driver):
            """
            Checks if CAPTCHA is present on the page.

            Args:
                driver (Driver): The Selenium WebDriver instance.

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

        # Initialize the Selenium WebDriver with the specified options
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,  # Use headless mode if specified
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="de",
            no_sandbox=True
        )

        driver.set_page_load_timeout(60)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(1, 2))  # Random sleep to avoid detection

  
        # Check for CAPTCHA before performing the search
        if not check_captcha(driver):
            try:
                search = driver.find_element(By.NAME, search_box)
                search.send_keys(query)
                search.send_keys(Keys.RETURN)
                time.sleep(random.randint(1, 2))  # Random sleep to avoid detection

            except Exception as e:
                print(f"Error occurred: {e}")
                search_results = -1
                return search_results

            # Retrieve initial search results and remove duplicates
            search_results = get_search_results(driver, page)
            if search_results:
                search_results = remove_duplicates(search_results)

            results_number = len(search_results)
            print(f"Initial search results count for '{query}': {results_number}")

            # If no results were found, retry with a new proxy
            if results_number == 0:
                print("No results found with the current proxy. Switching proxy.")
                driver.quit()
                time.sleep(random.randint(1, 2))  # Random sleep before reinitializing
                # Reinitialize the driver with a new proxy
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
                    no_sandbox=True,
                    proxy=proxy
                )

            # Continue scraping if results are fewer than the limit
            if results_number < limit:
                continue_scraping = True
                pagination_available = search_pagination(source=driver.page_source)

                if pagination_available:
                    print("Pagination found.")
                    # Click on next SERP pages until the result limit is reached
                    while results_number <= limit and page <= (limit / 10) and continue_scraping:
                        if not check_captcha(driver):
                            time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
                            page += 1
                            page_label = f"Page {page}"
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            try:
                                next_page_button = driver.find_element(By.XPATH, next_page.format(page_label))
                                next_page_button.click()
                                search_results += get_search_results(driver, page)
                                search_results = remove_duplicates(search_results)
                                results_number = len(search_results)
                            except Exception:
                                continue_scraping = False
                        else:
                            continue_scraping = False
                            search_results = -1

                    driver.quit()
                    return search_results

                else:
                    print("No pagination found.")
                    start = 0
                    query_formatted = query.lower().replace(" ", "+")
                    search_results = []
                    results_number = 0

                    while results_number <= limit and start <= limit and continue_scraping:
                        if not check_captcha(driver):
                            try:
                                edit_search_url = f"{get_search_url}{query_formatted}{language}&start={start}"
                                print(edit_search_url)
                                driver.set_page_load_timeout(120)
                                driver.implicitly_wait(60)
                                driver.get(edit_search_url)
                                time.sleep(random.randint(2, 4))  # Random sleep to avoid detection
                                page += 1
                                start += 10
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
                                print(f"Error occurred: {e}")
                                search_results = -1
                                continue_scraping = False
                        else:
                            continue_scraping = False
                            search_results = -1

                    driver.quit()
                    return search_results

            else:
                driver.quit()
                return search_results

        else:
            search_results = -1
            driver.quit()

    except Exception as e:
        print(f"Exception occurred: {e}")
        try:
            driver.quit()
        except Exception:
            pass
        search_results = -1
        return search_results
