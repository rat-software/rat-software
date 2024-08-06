from scrapers.requirements import *
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

def run(query, limit, scraping, headless):
    """
    Main function to run the web scraper.

    Parameters:
    query (str): Search query.
    limit (int): Maximum number of search results to retrieve.
    scraping (object): Scraping object with functions to scrape search engines.
    headless (bool): Whether to run the browser in headless mode.

    Returns:
    list: List of search results or -1 if CAPTCHA is encountered.
    """
    try:
        search_url = "https://duckduckgo.com/"
        search_box = "q"
        captcha = "g-reaptcha"
        next_page_xpath = "//button[@id='more-results']"
        results_number = 0
        page = 1
        search_results = []

        def get_search_results(driver, page):
            """
            Function to scrape search results from a SERP page.

            Parameters:
            driver (WebDriver): Selenium WebDriver.
            page (int): Current SERP page.

            Returns:
            list: List of search results.
            """
            counter = 0
            search_results = []

            time.sleep(10)
            source = driver.page_source
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, "lxml")

            for result in soup.find_all("li", class_="wLL07_0Xnd1QZpzpfR4W"):
                result_title = result.find("span", class_="EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk").text.strip() if result.find("span", class_="EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk") else "N/A"
                result_description = " ".join(result.find("div", class_="E2eLOJr8HctVnDOTM8fs").text.strip().replace(result_title, "").split()) if result.find("div", class_="E2eLOJr8HctVnDOTM8fs") else "N/A"
                result_url = result.find("a", class_="Rn_JXVtoPVAFyGkcaXyK").attrs['href'] if result.find("a", class_="Rn_JXVtoPVAFyGkcaXyK") else "N/A"

                if counter < limit + 2 and result_url != "N/A" and "http" in result_url:
                    search_results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
                    counter += 1

            return search_results

        def check_captcha(driver):
            """
            Function to check if CAPTCHA is present on the page.

            Parameters:
            driver (WebDriver): Selenium WebDriver.

            Returns:
            bool: True if CAPTCHA is present, False otherwise.
            """
            return captcha in driver.page_source

        def remove_duplicates(search_results):
            """
            Function to remove duplicate search results.

            Parameters:
            search_results (list): List of search results.

            Returns:
            list: List of unique search results.
            """
            cleaned_search_results = []
            url_list = {sr[2]: i for i, sr in enumerate(search_results)}

            for value in url_list.values():
                cleaned_search_results.append(search_results[value])

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
            locale_code="pl",
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        driver.get("https://duckduckgo.com/settings/")
        try:
            dropdown = Select(driver.find_element(By.CLASS_NAME, "frm__select__input.js-set-input"))
            dropdown.select_by_value('pl-pl')
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
                        next_button = driver.find_element(By.XPATH, next_page_xpath)
                        next_button.click()
                        time.sleep(random.randint(1, 2))
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
            driver.quit()
            return -1

    except Exception as e:
        print(str(e))
        try:
            driver.quit()
        except:
            pass
        return -1
