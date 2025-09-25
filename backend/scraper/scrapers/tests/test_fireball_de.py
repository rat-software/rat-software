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
def test_fireball_de():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="de-DE"
    )
    driver.set_page_load_timeout(30)


    try:
        driver.get("https://fireball.de")

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

        # 1. Accept cookie banner (if present)
        try:
            wait = WebDriverWait(driver, 10)
            cookie_accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@data-full-consent, 'true')]")))
            cookie_accept_button.click()
            print("Cookie banner accepted.")
        except TimeoutException:
            print("No cookie banner found or timeout reached.")
        except Exception as e:
            print(f"Error clicking cookie banner: {e}")

        # Find search box and start search
        try:
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box.send_keys("test" + Keys.RETURN)
            results["Search box (By.NAME = 'q')"] = True
        except Exception:
            results["Search box (By.NAME = 'q')"] = False
            print("Search box not found!")

       # Wait for results to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-result search-result-web")))
            results_elements = driver.find_elements(By.CSS_SELECTOR, "div.search-result search-result-web")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: Fireball results not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")


        # Check DOM elements
        selectors = {
            "Title (div.search-result-title)": (By.CSS_SELECTOR, "div.search-result-title"),
            "Description (div.search-result-text)": (By.CSS_SELECTOR, "div.search-result-text"),
            "Result link (a.search-result-url)": (By.CSS_SELECTOR, "a.search-result-url"),
            "Next page button (data-test-id=next-button)": (By.CSS_SELECTOR, "a[data-test-id='next-button']")
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
        assert results.get("Search box (By.NAME = 'q')"), "Search box was not found."
        
        required_elements = [
            "Title (div.search-result-title)",
            "Description (div.search-result-text)",
            "Result link (a.search-result-url)",
            "Next page button (data-test-id=next-button)"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_fireball_de()
    print("Test completed!")
