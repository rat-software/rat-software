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

def reliable_send_keys(driver, text, max_attempts=3):
    """
    Tries to reliably enter text into the search box.
    Retries if the input disappears due to DOM or JS interference.
    """
    for attempt in range(max_attempts):
        try:
            search_box = driver.find_element(By.NAME, "q")
            search_box.clear()
            search_box.send_keys(text)
            time.sleep(0.5)  # Let the DOM update

            # Verify if the input was set correctly
            if search_box.get_attribute("value") == text:
                print(f"Text successfully entered on attempt {attempt + 1}.")
                return True
            else:
                print(f"Input not correctly set on attempt {attempt + 1}. Retrying...")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(1)
    return False

@pytest.mark.selenium
def test_dogpile_de():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="de-DE"
    )
    driver.set_page_load_timeout(30)

    try:
        driver.get("https://www.dogpile.com/")

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
            cookie_accept_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='onetrust-accept-btn-handler']"))
            )
            driver.execute_script("arguments[0].click();", cookie_accept_button)
            print("Cookie banner accepted.")
        except TimeoutException:
            print("No cookie banner found or timeout reached.")
        except Exception as e:
            print(f"Error clicking cookie banner: {e}")

        # 2. Locate search box and perform a search
        try:
            wait.until(EC.element_to_be_clickable((By.NAME, "q")))
            print("Search box found and clickable.")
            results["Search box (By.NAME = 'q')"] = True
        except TimeoutException:
            print("Timeout: Search box not clickable or not found.")
            results["Search box (By.NAME = 'q')"] = False
            
        # 2b. Enter text and press ENTER
        if results["Search box (By.NAME = 'q')"]:
            success = reliable_send_keys(driver, "test")
            if success:
                try:
                    # Find the search box again to send RETURN key for a stable submission
                    driver.find_element(By.NAME, "q").send_keys(Keys.RETURN)
                    print("Pressed ENTER to submit the form.")
                except Exception as e:
                    print(f"Error while pressing RETURN: {e}")
            else:
                print("Failed to reliably enter text into the search box.")


        # 3. Wait for search results to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='web-yahoo__result']")))
            results_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='web-yahoo__result']")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: 'web-yahoo__result' not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")


         # Check for key result DOM elements with debug output
        selectors = {
            "web-yahoo__result container": (By.CSS_SELECTOR, "div.web-yahoo__result"),
            "Title (a.web-yahoo__title)": (By.CSS_SELECTOR, "a.web-yahoo__title"),
            "Description (span.web-yahoo__description)": (By.CSS_SELECTOR, "span.web-yahoo__description"),
            "All links in results (a[href])": (By.CSS_SELECTOR, "div.web-yahoo__result a[href]"),
            "Next-Page-Button (XPath)": (By.XPATH, "//a[contains(@class, 'pagination__num--next')]"),
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
            "web-yahoo__result container",
            "Title (a.web-yahoo__title)",
            "Description (span.web-yahoo__description)",
            "All links in results (a[href])",
            "Next-Page-Button (XPath)"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    test_dogpile_de()
    print("Test completed!")
