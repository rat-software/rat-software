from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import time
import random

def run(query, limit, scraping, headless):
    """
    Main function to run a scraper.

    Args:
        query (str): Search query.
        limit (int): Maximum number of results to query.
        scraping (object): Scraping object with functions to scrape the search engines.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        list: A list of search results, each containing title, description, URL, 
              encoded HTML source, encoded screenshot, and page number.
    """
    try:
        # Search engine configuration
        search_url = "https://duckduckgo.com/"
        search_box = "q"
        captcha = "g-reaptcha"
        next_page_xpath = "//button[@id='more-results']"
        
        # Initialize variables
        results_number = 0
        page = 1
        search_results = []

        # Define custom functions
        def get_search_results(driver, page):
            """
            Scrapes search results from the current page.

            Args:
                driver (object): Selenium web driver.
                page (int): SERP page number.

            Returns:
                list: A list of search results.
            """
            results = []
            source = driver.page_source
            time.sleep(10)  # wait for the page to load completely
            
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            
            soup = BeautifulSoup(source, features="lxml")
            for result in soup.find_all("li", class_=["wLL07_0Xnd1QZpzpfR4W"]):
                try:
                    result_title = result.find("span", class_=["EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk"]).text.strip()
                except:
                    result_title = "N/A"

                try:
                    result_description = " ".join(result.find("div", class_=["E2eLOJr8HctVnDOTM8fs"]).text.strip().split())
                except:
                    result_description = "N/A"

                try:
                    result_url = result.find("a", class_=["Rn_JXVtoPVAFyGkcaXyK"])['href']
                except:
                    result_url = "N/A"

                if result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
            
            return results

        def check_captcha(driver):
            """
            Checks if the search engine shows a CAPTCHA.

            Args:
                driver (object): Selenium web driver.

            Returns:
                bool: True if CAPTCHA is detected, False otherwise.
            """
            source = driver.page_source
            return captcha in source

        def remove_duplicates(results):
            """
            Removes duplicate search results.

            Args:
                results (list): List of search results.

            Returns:
                list: List of unique search results.
            """
            unique_results = []
            seen_urls = set()
            for result in results:
                if result[2] not in seen_urls:
                    unique_results.append(result)
                    seen_urls.add(result[2])
            return unique_results

        # Initialize the web driver
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
            locale_code="en-GB",
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        # Set search engine language to French
        driver.get("https://duckduckgo.com/settings/")
        try:
            dropdown = Select(driver.find_element(By.CLASS_NAME, "frm__select__input.js-set-input"))
            dropdown.select_by_value('uk-en')
        except Exception as e:
            print(str(e))

        driver.get(search_url)
        time.sleep(random.randint(1, 2))

        # Start scraping if no CAPTCHA
        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(random.randint(1, 2))

            search_results = get_search_results(driver, page)
            search_results = remove_duplicates(search_results)
            results_number = len(search_results)

            # Continue scraping next pages
            while results_number <= limit and page <= (limit / 10):
                if not check_captcha(driver):
                    time.sleep(random.randint(1, 2))
                    page += 1
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    try:
                        next_button = driver.find_element(By.XPATH, next_page_xpath)
                        next_button.click()
                        time.sleep(random.randint(1, 2))
                        search_results += get_search_results(driver, page)
                        search_results = remove_duplicates(search_results)
                        results_number = len(search_results)
                    except Exception as e:
                        break
                else:
                    search_results = -1
                    break

            driver.quit()
            return search_results

        else:
            driver.quit()
            return -1

    except Exception as e:
        print(str(e))
        try:
            driver.quit()
        except:
            pass
        return -1
