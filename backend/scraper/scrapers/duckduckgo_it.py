from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import random


def run(query, limit, scraping, headless):
    """
    Main function to run the scraper for the search engine.

    Args:
    query (str): The search query.
    limit (int): Maximum number of results to retrieve.
    scraping: Scraping object with functions to scrape the search engines.
    headless (bool): Run browser in headless mode.

    Returns:
    list: List of search results or -1 if scraping was blocked by CAPTCHA.
    """
    try:
        # Define parameters for scraping the search engine
        search_url = "https://duckduckgo.com/"
        search_box = "q"
        captcha = "g-recaptcha"
        next_page = "//button[@id='more-results']"
        results_number = 0
        page = 1
        search_results = []

        def get_search_results(driver, page):
            """
            Retrieve search results from the current page.

            Args:
            driver: Selenium WebDriver instance.
            page (int): Current SERP page.

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

            for result in soup.find_all("li", class_=["wLL07_0Xnd1QZpzpfR4W"]):
                result_title = "N/A"
                result_description = "N/A"
                result_url = "N/A"

                try:
                    result_title = result.find("span", class_=["EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk"]).text.strip()
                except:
                    pass

                try:
                    descriptions = result.find_all("div", class_=["E2eLOJr8HctVnDOTM8fs"])
                    result_description = " ".join(desc.text.strip().replace(result_title, " ") for desc in descriptions)
                except:
                    pass

                try:
                    result_url = result.find("a", class_=["Rn_JXVtoPVAFyGkcaXyK"]).attrs['href']
                except:
                    pass

                if counter < limit + 2 and result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
                    counter += 1

            return results

        def check_captcha(driver):
            """
            Check if the search engine has shown a CAPTCHA.

            Args:
            driver: Selenium WebDriver instance.

            Returns:
            bool: True if CAPTCHA is detected, otherwise False.
            """
            return captcha in driver.page_source

        def remove_duplicates(search_results):
            """
            Remove duplicate search results based on URLs.

            Args:
            search_results (list): List of search results.

            Returns:
            list: Cleaned list of search results.
            """
            cleaned_search_results = []
            url_set = set()
            for result in search_results:
                url = result[2]
                if url not in url_set:
                    url_set.add(url)
                    cleaned_search_results.append(result)
            return cleaned_search_results

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
            locale_code="it",
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        driver.get("https://duckduckgo.com/settings/")
        try:
            dropdown = Select(driver.find_element(By.CLASS_NAME, "frm__select__input.js-set-input"))
            dropdown.select_by_value('it-it')
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

            continue_scraping = True

            while results_number <= limit and page <= (limit / 10) and continue_scraping:
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
        print(str(e))
        try:
            driver.quit()
        except:
            pass
        return -1
