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
        query (str): The search query.
        limit (int): Maximum number of results to retrieve.
        scraping (object): Scraping object with utility functions.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        list: List of search results or -1 if CAPTCHA is detected.
    """
    try:
        search_url = "https://duckduckgo.com/"
        search_box = "q"
        captcha = "g-recaptcha"
        next_page = "//button[@id='more-results']"
        results_number = 0
        page = 1
        search_results = []

        def get_search_results(driver, page):
            """
            Scrapes search results from the search engine.

            Args:
                driver (WebDriver): The Selenium WebDriver instance.
                page (int): The current search results page number.

            Returns:
                list: List of search results.
            """
            counter = 0
            results = []

            source = driver.page_source
            time.sleep(10)

            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")


            for result in soup.find_all("li", class_="wLL07_0Xnd1QZpzpfR4W"):
                try:
                    result_title = result.find("a", attrs={"data-testid": "result-title-a"}).text.strip()
                except:
                    result_title = "N/A"

                try:
                    result_description = result.find("div", attrs={"data-result": "snippet"}).text.strip()
                except:
                    result_description = "N/A"

                try:
                    result_url = result.find("a", attrs={"data-testid": "result-extras-url-link"})['href']
                except:
                    result_url = "N/A"

                if result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
            return results

        def check_captcha(driver):
            """
            Checks if a CAPTCHA is present on the page.

            Args:
                driver (WebDriver): The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, False otherwise.
            """
            return captcha in driver.page_source

        def remove_duplicates(results):
            """
            Removes duplicate search results.

            Args:
                results (list): List of search results.

            Returns:
                list: List of unique search results.
            """
            url_dict = {result[2]: result for result in results}
            return list(url_dict.values())

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
            locale_code="nl"
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        # Set DuckDuckGo region and language via settings
        driver.get("https://duckduckgo.com/settings/")

        try:
            region_dropdown = Select(driver.find_element(By.ID, "setting_kl"))
            region_dropdown.select_by_value("nl-nl")
            language_dropdown = Select(driver.find_element(By.ID, "setting_kad"))
            language_dropdown.select_by_value("nl_NL")
        except Exception as e:
            print(str(e))

        driver.get(search_url)
        time.sleep(random.randint(1, 2))

        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(random.randint(1, 2))

            search_results = get_search_results(driver, page)
            search_results = remove_duplicates(search_results)
            results_number = len(search_results)

            while results_number <= limit and page <= (limit / 10):
                if not check_captcha(driver):
                    time.sleep(random.randint(1, 2))
                    page += 1
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    try:
                        next_btn = driver.find_element(By.XPATH, next_page)
                        next_btn.click()
                        time.sleep(random.randint(1, 2))
                        search_results += get_search_results(driver, page)
                        search_results = remove_duplicates(search_results)
                        results_number = len(search_results)
                    except Exception:
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
