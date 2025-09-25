import time
import sys
import os
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scrapers.requirements import *

@pytest.mark.selenium
def test_econbiz_de():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="de-DE"
    )
    driver.set_page_load_timeout(30)

    try:
        driver.get("https://www.econbiz.de/")

        results = {}

        # Check for CAPTCHA immediately after loading the page
        try:
            page_source = driver.page_source.lower()
            captcha_keywords = ["captcha", "recaptcha", "are-you-human", "cf-challenge", "sec-check"]
            captcha_present = any(keyword in page_source for keyword in captcha_keywords)
            results["CAPTCHA detected (keyword-scan)"] = captcha_present

            if captcha_present:
                print("CAPTCHA detected in page source.")

                try:
                    driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
                    print("CAPTCHA-iframe found.")
                    results["CAPTCHA iframe present"] = True
                except:
                    results["CAPTCHA iframe present"] = False

            else:
                print("No CAPTCHA detected.")
                results["CAPTCHA iframe present"] = False

        except Exception as e:
            print(f"Error during CAPTCHA check: {e}")
            results["CAPTCHA check failed"] = False

        # Find search box and start search
        try:
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "lookfor")))
            search_box.send_keys("test" + Keys.RETURN)
            results["Search box (By.NAME = 'lookfor')"] = True
        except Exception:
            results["Search box (By.NAME = 'lookfor')"] = False
            print("Search box not found!")

       # Wait for results to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-sm-10.col-xs-9.result-content")))
            results_elements = driver.find_elements(By.CSS_SELECTOR, "div.col-sm-10.col-xs-9.result-content")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: result-content not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")


        # Check DOM elements
        selectors = {
            "Title (span[property='schema:headline'])": (By.CSS_SELECTOR, "span[property='schema:headline']"),
            "Description (div.snippets)": (By.CSS_SELECTOR, "div[class*='snippets']"),
            "Result link (a.title.print-no-url)": (By.CSS_SELECTOR, "a.title.print-no-url"),
            "Next page button (//span[@class='icon-inline econ-right'])": (By.XPATH, "//span[@class='icon-inline econ-right']")
        }

        for label, (by, selector) in selectors.items():
            try:
                elems = driver.find_elements(by, selector)
                print(f"{label}: Number of elements = {len(elems)}")
                results[label] = len(elems) > 0
            except Exception as e:
                print(f"Error checking {label}: {e}")
                results[label] = False

        # Final result report
        print("\nTest Results:")
        for label, result in results.items():
            if label.startswith("CAPTCHA"):
                status = "Yes" if result else "No"
            else:
                status = "OK" if result else "FAIL"
            print(f"{label}: {status}")

        # Assertions
        assert not results.get("CAPTCHA detected (keyword-scan)"), "CAPTCHA was detected, test aborted"
        assert results.get("Search box (By.NAME = 'lookfor')"), "Search box was not found."
        
        required_elements = [
            "Title (span[property='schema:headline'])",
            "Description (div.snippets)",
            "Result link (a.title.print-no-url)",
            "Next page button (//span[@class='icon-inline econ-right'])"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_econbiz_de()
    print("Test completed!")
