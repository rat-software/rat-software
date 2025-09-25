import time
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scrapers.requirements import *

def run_test():
    region_code = "en-us"        
    region_label = "United States (English)" 
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=False, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="en-US"
    )

    # options.add_argument("--headless=new")  # Visibility optional
    driver.set_page_load_timeout(30)

    try:
        driver.get("https://www.ecosia.org/")
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
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            )
            driver.execute_script("arguments[0].click();", cookie_accept_button)
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
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.result__body")))
            results_elements = driver.find_elements(By.CSS_SELECTOR, "div.result__body")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: 'div.result__body' not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")
        
        try:
            print("INFO: Looking for the 'Search region:' button...")
            
            region_button_selector = (By.XPATH, "//button[.//span[contains(text(), 'Search region:')]]")
            region_button = wait.until(EC.element_to_be_clickable(region_button_selector))
            driver.execute_script("arguments[0].click();", region_button)
            print("INFO: Region dropdown opened.")
            
            option_selector = (By.CSS_SELECTOR, f"li[data-test-id='search-regions-region-{region_code}']")
            option = wait.until(EC.element_to_be_clickable(option_selector))
            
            print(f"INFO: Region option '{region_label}' found. Clicking...")
            option.click()
            
            print(f"SUCCESS: Region '{region_label}' has been selected.")
            print("INFO: Waiting for 5 seconds to observe the result...")
            time.sleep(5)
        except Exception as e:
            print(f"WARNING: Unable to change region to '{region_label}'. Continuing with default settings. Error: {e}")
        
        try:
            region_button_text = driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Search region:')]]").text
            if region_label in region_button_text:
                results[f"Region set to {region_code.upper()}"] = True
            else:
                results[f"Region set to {region_code.upper()}"] = False
                print(f"Region not correctly set, found text: {region_button_text}")
        except Exception as e:
            print(f"Error reading region button: {e}")
            results[f"Region set to {region_code.upper()}"] = False


        # Check DOM elements
        selectors = {
            "Result body (div.result--web, article.card-web, div.result__body)": (By.CSS_SELECTOR, "div.result--web, article.card-web, div.result__body"),
            "Title (a.result-title, h2 a, div.result__title)": (By.CSS_SELECTOR, "a.result-title, h2 a, div.result__title"), 
            "Description (p.result-snippet, div.result-snippet, div.result__description)": (By.CSS_SELECTOR, "p.result-snippet, div.result-snippet, div.result__description"),
            "Result link (a.result-title, a.result-url, h2 a, a.result__link)": (By.CSS_SELECTOR, "a.result-title, a.result-url, h2 a, a.result__link"), 
            "Next page button (data-test-id=next-button)": (By.CSS_SELECTOR, "a[data-test-id='next-button']"),
            "Region button (Suchgebiet)": (By.XPATH, "//button[.//span[contains(text(), 'Search region:')]]")
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
        assert not results.get("CAPTCHA detected (keyword-scan)"), "CAPTCHA detected, test aborted."
        assert results.get("Search box (By.NAME = 'q')"), "Search box not found."

        required_elements = [
            "Result body (div.result--web, article.card-web, div.result__body)",
            "Title (a.result-title, h2 a, div.result__title)",
            "Description (p.result-snippet, div.result-snippet, div.result__description)",
            "Result link (a.result-title, a.result-url, h2 a, a.result__link)",
            "Next page button (data-test-id=next-button)",
            "Region button (Suchgebiet)"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' not found."
        
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    run_test()
    print("Test completed!")


