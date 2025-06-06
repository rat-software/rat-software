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
from fake_useragent import UserAgent




def run(query, limit, scraping, headless):
    """
    Scrapes Google search results based on the provided query.

    Args:
        query (str): The search query to use.
        limit (int): The maximum number of search results to retrieve.
        scraping (Scraping): An instance of the Scraping class used for encoding and taking screenshots.
        headless (bool): If True, run the browser in headless mode (without GUI).

    Returns:
        list: A list of search results, where each result is a list containing the title, description, URL, 
              and metadata (encoded page source and screenshot binary). Returns -1 if CAPTCHA is detected 
              or if an error occurs during scraping.
    """
    try:

        # Initialize the list for proxies
        proxies = []

        # Get the directory path to locate the proxy file
        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        
        # Load proxies from a CSV file
        with open(os.path.join(currentdir, 'proxies', 'UK.csv')) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                proxies.append(row)

        # Shuffle the proxies and select one
        random.shuffle(proxies)
        proxy = proxies[0][0] if proxies else None

        # Define constants for scraping
        search_url = "https://www.google.com/webhp?hl=en&gl=GB&&uule=w+CAIQICIOVW5pdGVkIEtpbmdkb20="  # URL for Google search
        search_box = "q"  # Name attribute of the search input box
        captcha = "g-recaptcha"  # Indicator for CAPTCHA presence
        next_page_xpath = "//a[@aria-label='{}']"  # XPath template for the "next" button
        next_scroll_xpath = "//span[@class='RVQdVd']"  # XPath for scrolling additional search results
        results_number = 0  # Initialize count of search results
        page = 1  # Initialize page number
        search_results = []  # Initialize list to store search results
        get_search_url = "https://www.google.com/search?q="  # Base URL for search results

        limit = limit+10
        print(f"Limit set to: {limit}")
            
        # Function to determine if pagination is available on the search results page
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

        # Function to scrape search results from the current page
        def get_search_results(driver, page):
            """
            Extracts search results from the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of search results, each containing the title, description, URL, and metadata.
            """
            results = []
            source = driver.page_source

            # Encode the page source and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, features="lxml")

            # Remove undesired elements from the page
            undesired_classes = ["d4rhi", "Wt5Tfe", "UDZeY fAgajc OTFaAf"]
            for cls in undesired_classes:
                for element in soup.find_all("div", class_=cls):
                    element.extract()

            # Extract search results
            for result in soup.find_all("div", class_=["tF2Cxc", "dURPMd"]):
                result_title = ""
                result_description = ""
                result_url = ""

                # Extract the title
                try:
                    title_element = result.find("h3", class_=["LC20lb", "MBeuO", "DKV0Md"])
                    if title_element:
                        result_title = title_element.text.strip()
                except Exception:
                    result_title = "N/A"

                # Extract the description
                try:
                    description_element = result.find("div", class_=re.compile("VwiC3b", re.I))
                    if description_element:
                        result_description = description_element.text.strip()
                except Exception:
                    result_description = "N/A"

                # Extract URL
                try:
                    urls = result.find_all("a")
                    if urls:
                        url = urls[0].attrs.get('href', "N/A")
                        result_url = url
                except Exception:
                    result_url = "N/A"

                # Add the result if URL is valid
                if result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return results

        # Function to check if CAPTCHA is present on the page
        def check_captcha(driver):
            """
            Checks if a CAPTCHA is present on the page.

            Args:
                driver (Driver): The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is present, False otherwise.
            """
            source = driver.page_source
            return captcha in source

        # Function to remove duplicate search results based on the URL
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

            for result in search_results:
                url = result[2]
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)

            return unique_results

        # Initialize Selenium WebDriver

        ua = UserAgent(platforms='pc', browsers='chrome')

        # Get a random browser user-agent string
        user_agent = ua.random
        print(user_agent)

        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,  # Run in headless mode if specified
            incognito=False,
            agent=user_agent,
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="en-GB",  # Set locale to US English
            no_sandbox=True
        )

        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(1, 2))  # Random sleep to avoid quick automatic blocking

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            search_box_element = driver.find_element(By.NAME, search_box)
            search_box_element.send_keys(query)
            search_box_element.send_keys(Keys.RETURN)
            time.sleep(random.randint(1, 2))  # Random sleep to avoid detection

            # Get initial search results and remove duplicates
            search_results = get_search_results(driver, page)
            search_results = remove_duplicates(search_results)
            results_number = len(search_results)

            print(f"Initial number of search results for '{query}': {results_number}")

            # If no results were found, retry with a new proxy
            if results_number == 0 and proxy:
                print("No results found with the current proxy. Switching proxy.")
                driver.quit()
                time.sleep(random.randint(1, 2))  # Random sleep before reinitializing
                # Reinitialize the driver with a new proxy
                driver = Driver(
                    browser="chrome",
                    wire=True,
                    uc=True,
                    headless2=headless,  # Run in headless mode if specified
                    incognito=False,
                    agent=user_agent,
                    do_not_track=True,
                    undetectable=True,
                    extension_dir=ext_path,
                    locale_code="en-GB",  # Set locale to US English
                    no_sandbox=True,
                    proxy=proxy
                )

            # Continue scraping if the number of results is less than the limit
            if results_number < limit:
                continue_scraping = True
                pagination_available = search_pagination(source=driver.page_source)

                if pagination_available:
                    print("Pagination found.")
                    # Click on the "next" button to navigate through search result pages
                    while results_number <= limit and page <= (limit / 10) and continue_scraping:
                        if not check_captcha(driver):
                            time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
                            page += 1
                            page_label = f"Page {page}"
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            try:
                                next_button = driver.find_element(By.XPATH, next_page_xpath.format(page_label))
                                next_button.click()
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
                    query = query.lower().replace(" ", "+")
                    search_results = []
                    results_number = 0

                    # Scrape results by updating the URL with different start parameters
                    while results_number <= limit and start <= limit and continue_scraping:
                        if not check_captcha(driver):
                            try:
                                edit_search_url = f"{get_search_url}{query}&start={start}"
                                print(edit_search_url)
                                driver.get(edit_search_url)
                                time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
                                page += 1
                                start += 10
                                extract_search_results = get_search_results(driver, page)

                                if extract_search_results:
                                    print("Appending results.")
                                    search_results += extract_search_results
                                    search_results = remove_duplicates(search_results)
                                    results_number = len(search_results)
                                else:
                                    continue_scraping = False

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
        except:
            pass
        search_results = -1
        return search_results
