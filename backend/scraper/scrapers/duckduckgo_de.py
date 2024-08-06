from scrapers.requirements import *
from bs4 import BeautifulSoup
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

def run(query, limit, scraping, headless):
    """
    Main function to scrape search results from DuckDuckGo.

    Parameters:
    query (str): The search query.
    limit (int): Maximum number of results to query.
    scraping (object): Scraping object with helper functions for scraping.
    headless (bool): Run the browser in headless mode if True.

    Returns:
    list: A list of search results with title, description, URL, serp_code, serp_bin, and page number.
    """
    try:
        # Configuration for the search engine and initial setup
        search_url = "https://duckduckgo.com/"
        search_box = "q"
        captcha_indicator = "g-recaptcha"
        next_page_xpath = "//button[@id='more-results']"
        results_number = 0
        page = 1
        search_results = []

        def get_search_results(driver, page):
            """
            Retrieve search results from the search engine result page (SERP).

            Parameters:
            driver (object): Selenium WebDriver instance.
            page (int): SERP page number.

            Returns:
            list: A list of search results for the current page.
            """
            results = []
            source = driver.page_source
            time.sleep(10)  # Ensure the page has fully loaded
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, features="lxml")

            for result in soup.find_all("li", class_="wLL07_0Xnd1QZpzpfR4W"):
                try:
                    result_title = result.find("span", class_="EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk").text.strip()
                except:
                    result_title = "N/A"

                try:
                    result_description = " ".join([desc.text.strip() for desc in result.find_all("div", class_="E2eLOJr8HctVnDOTM8fs")])
                except:
                    result_description = "N/A"

                try:
                    result_url = result.find("a", class_="Rn_JXVtoPVAFyGkcaXyK")['href']
                except:
                    result_url = "N/A"

                if result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
            return results

        def check_captcha(driver):
            """
            Check if the search engine has presented a CAPTCHA.

            Parameters:
            driver (object): Selenium WebDriver instance.

            Returns:
            bool: True if CAPTCHA is detected, otherwise False.
            """
            return captcha_indicator in driver.page_source

        def remove_duplicates(results):
            """
            Remove duplicate search results.

            Parameters:
            results (list): List of search results.

            Returns:
            list: List of unique search results.
            """
            seen_urls = set()
            unique_results = []
            for result in results:
                if result[2] not in seen_urls:
                    seen_urls.add(result[2])
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
            locale_code="de",
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        # Set DuckDuckGo to German
        driver.get("https://duckduckgo.com/settings/")
        try:
            dropdown = Select(driver.find_element(By.CLASS_NAME, "frm__select__input.js-set-input"))
            dropdown.select_by_value('de-de')
        except Exception as e:
            print(f"Language setting failed: {e}")

        driver.get(search_url)
        time.sleep(random.randint(1, 2))

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(random.randint(1, 2))

            search_results = get_search_results(driver, page)
            search_results = remove_duplicates(search_results)
            results_number = len(search_results)

            # Continue scraping additional pages
            continue_scraping = True
            while results_number <= limit and page <= (limit / 10) and continue_scraping:
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
                    except:
                        continue_scraping = False
                else:
                    continue_scraping = False
                    search_results = -1

            driver.quit()
            return search_results

        else:
            driver.quit()
            return -1

    except Exception as e:
        print(f"Scraping failed: {e}")
        try:
            driver.quit()
        except:
            pass
        return -1

    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Driver quit failed: {e}")
