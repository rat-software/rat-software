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
def test_brave_de():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="de-DE"
    )
    driver.set_page_load_timeout(30)

    try:
        driver.get("https://search.brave.com/")

        results = {}

        # Check for CAPTCHA immediately after loading the page
        try:
            page_source = driver.page_source.lower()
            captcha_keywords = ["are-you-human", "cf-challenge", "sec-check"]
            iframe_indicators = ["iframe", "recaptcha", "challenge"]
            captcha_present = (
                any(keyword in page_source for keyword in captcha_keywords) and
                any(ind in page_source for ind in iframe_indicators)
            )
            results["CAPTCHA detected (keyword-scan)"] = captcha_present

            try:
                iframe = driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
                if iframe.is_displayed():
                    print("CAPTCHA iframe is visible.")
                    results["CAPTCHA iframe present"] = True
                else:
                    print("CAPTCHA iframe is hidden.")
                    results["CAPTCHA iframe present"] = False
            except NoSuchElementException:
                results["CAPTCHA iframe present"] = False

        except Exception as e:
            print(f"Error during CAPTCHA check: {e}")
            results["CAPTCHA check failed"] = False

       # 2. Locate search box and perform a search
        try:
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box.clear()
            search_box.send_keys("test")
            
            # Versuche zunächst RETURN
            try:
                search_box.send_keys(Keys.RETURN)
                results["Search box (By.NAME = 'q')"] = True
            except Exception:
                results["Search box (By.NAME = 'q')"] = False
                print("RETURN failed, trying submit button.")

                try:
                    submit_button = wait.until(EC.element_to_be_clickable((By.ID, "submit-button")))
                    submit_button.click()
                    results["Submit button (id='submit-button')"] = True
                except Exception:
                    results["Submit button (id='submit-button')"] = False
                    print("Submit button not found or not clickable!")
        except Exception:
            results["Search box (By.NAME = 'q')"] = False
            print("Search box not found!")

        # 3. Wait for search results to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='snippet']")))
            results_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='snippet']")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: 'div.snippet' not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")

        # Check for key result DOM elements with debug output
        selectors = {
            "snippet container (div.snippet...)": (By.CSS_SELECTOR, "div[class^='snippet']"),
            "heading-serpresult (div[class*='heading-serpresult'])": (By.XPATH, "//*[contains(@class, 'heading-serpresult')]"),
            "snippet-description (div.snippet-description)": (By.CSS_SELECTOR, "div.snippet-description"),
            "a[href]": (By.CSS_SELECTOR, "div[class^='snippet'] a[href]"),
            "next button (link text)": (By.LINK_TEXT, "Nächste"),
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

       # Nur wirklich abbrechen, wenn CAPTCHA sichtbar ist
        assert not (results.get("CAPTCHA detected (keyword-scan)") and results.get("CAPTCHA iframe present")), "Visible CAPTCHA was detected, test aborted"
        assert results.get("Search box (By.NAME = 'q')"), "Search box was not found."
        
        required_elements = [
            "snippet container (div.snippet...)",
            "heading-serpresult (div[class*='heading-serpresult'])",
            "snippet-description (div.snippet-description)",
            "a[href]",
            "next button (link text)"
            
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_brave_de()
    print("Test completed!")
