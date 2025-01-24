from scrapers.requirements import *
from bs4 import BeautifulSoup
import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def run(query, limit, scraping, headless):
    """
    Main function to scrape search results from a search engine.
    
    Parameters:
    query (str): The search query.
    limit (int): Maximum number of results to query.
    scraping (object): Scraping object with helper functions for scraping.
    headless (bool): Run the browser in headless mode if True.
    
    Returns:
    list: A list of search results with title, description, URL, serp_code, serp_bin, and page number.
    """
    try:
        search_url = "https://search.brave.com/"
        search_box = "q"
        captcha = "g-recaptcha"
        next_page = "Nächste"
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
            soup = BeautifulSoup(source, features="lxml")

            serp_code = scraping.encode_code(driver.page_source)
            serp_bin = scraping.take_screenshot(driver)

            for result in soup.find_all("div", class_=lambda x: x and x.startswith('snippet svelte')):
                result_title = "N/A"
                result_description = "N/A"
                result_url = "N/A"

                try:
                    result_title = result.find("div", class_=re.compile("heading-serpresult", re.I)).text.strip()
                except:
                    pass

                try:
                    description_tags = result.find_all("div", class_="snippet-description")
                    result_description = " ".join([desc.text.strip() for desc in description_tags])
                except:
                    pass

                try:
                    result_url = result.find("a")['href']
                except:
                    pass

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
            return captcha in driver.page_source

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
        driver.get(search_url)
        time.sleep(random.randint(2, 5))

        if not check_captcha(driver):
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(random.randint(2, 5))

            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            while (results_number < limit) and not check_captcha(driver):
                time.sleep(random.randint(2, 5))
                page += 1
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    next_button = driver.find_element(By.LINK_TEXT, next_page)
                    next_button.click()
                    search_results += get_search_results(driver, page)
                    results_number = len(search_results)
                except:
                    break

        driver.quit()
        return search_results if search_results else -1

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
