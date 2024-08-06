from scrapers.requirements import *
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import random


def run(query, limit, scraping, headless):
    """
    Main function to run a scraper for DuckDuckGo search engine.

    Parameters:
    query (str): Search query.
    limit (int): Maximum number of results to query.
    scraping (object): Scraping object with functions to scrape the search engines.
    headless (bool): Whether to run the browser in headless mode.

    Returns:
    list: A list of search results or -1 if scraping was blocked by CAPTCHA.
    """
    try:
        # Define parameters for scraping the search engine
        search_url = "https://duckduckgo.com/"
        search_box = "q"
        captcha = "g-recaptcha"
        next_page_xpath = "//button[@id='more-results']"
        search_results = []
        page = 1

        def get_search_results(driver, page):
            """
            Scrapes search results from the current page.

            Parameters:
            driver (object): Selenium WebDriver instance.
            page (int): Current SERP page number.

            Returns:
            list: List of search results with title, description, URL, serp_code, serp_bin, and page.
            """
            time.sleep(10)
            source = driver.page_source
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, 'lxml')
            results = []

            for result in soup.find_all("li", class_="wLL07_0Xnd1QZpzpfR4W"):
                try:
                    result_title = result.find("span", class_="EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk").text.strip()
                except:
                    result_title = "N/A"

                try:
                    result_description = " ".join(result.find("div", class_="E2eLOJr8HctVnDOTM8fs").text.strip().split())
                    result_description = result_description.replace(result_title, " ")
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
            Checks if the search engine has shown a CAPTCHA.

            Parameters:
            driver (object): Selenium WebDriver instance.

            Returns:
            bool: True if CAPTCHA is detected, False otherwise.
            """
            return captcha in driver.page_source

        def remove_duplicates(results):
            """
            Removes duplicate search results.

            Parameters:
            results (list): List of search results.

            Returns:
            list: Cleaned list of search results without duplicates.
            """
            seen_urls = set()
            cleaned_results = []

            for result in results:
                url = result[2]
                if url not in seen_urls:
                    seen_urls.add(url)
                    cleaned_results.append(result)

            return cleaned_results

        # Initialize Selenium WebDriver
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
            locale_code="sv",
        )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        # Set DuckDuckGo to Swedish locale
        driver.get("https://duckduckgo.com/settings/")
        try:
            dropdown = Select(driver.find_element(By.CLASS_NAME, "frm__select__input.js-set-input"))
            dropdown.select_by_value('se-sv')
        except Exception as e:
            print(str(e))

        # Start the search
        driver.get(search_url)
        time.sleep(random.randint(1, 2))

        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(random.randint(1, 2))

            search_results = get_search_results(driver, page)
            search_results = remove_duplicates(search_results)

            # Loop through additional pages if necessary
            while len(search_results) < limit and page <= (limit / 10):
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
