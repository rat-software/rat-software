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
def test_bing_se():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="sv-SE"
    )
    driver.set_page_load_timeout(30)

    try:
        driver.get("https://www.bing.com/?cc=se&setLang=sv")

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
                EC.element_to_be_clickable((By.CLASS_NAME, "bnp_btn_accept"))
            )
            driver.execute_script("arguments[0].click();", cookie_accept_button)
            print("Cookie banner accepted.")
        except TimeoutException:
            print("No cookie banner found or timeout reached.")
        except Exception as e:
            print(f"Error clicking cookie banner: {e}")

        # 2. Locate search box and perform a search
        try:
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys("test" + Keys.RETURN)
            results["Search box (By.NAME = 'q')"] = True
        except NoSuchElementException:
            results["Search box (By.NAME = 'q')"] = False
            print("Search box not found!")

        # 3. Wait for search results to load
        try:
            wait.until(EC.presence_of_element_located((By.ID, "b_results")))
            results_elements = driver.find_elements(By.ID, "b_results")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: 'b_results' not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")

        # Check for key result DOM elements with debug output   
        selectors = {
            "b_algo (li.b_algo) b_algo_group (li.b_algo_group)": (By.CSS_SELECTOR, "span.algoSlug_icon ,li.b_algoBigWiki, li.b_algo, li.b_algo_group"),
            "h2->a (li > h2 > a)": (By.CSS_SELECTOR, "li.b_algo h2 a, li.b_algo_group h2 a"),
            "tilk (a.tilk)": (By.CSS_SELECTOR, "a.tilk"),
            "tilk.tptt (a.tilk div.tptt)": (By.CSS_SELECTOR, "a.tilk div.tptt"),
            "Fallback a (li.b_algo a)": (By.CSS_SELECTOR, "li.b_algo a"),
            "Description (p.b_lineclamp*)": (By.CSS_SELECTOR, "p[class*='b_lineclamp']"),
            "Next page (title=Nächste Seite)": (By.CSS_SELECTOR, "a[title='Nästa sida']"),
            "Next page (class)": (By.CSS_SELECTOR, "a.sb_pagN, a.sb_pagN_bp, a.b_widePag, a.sb_bp"),
            "Next page (aria-label=Nächste)": (By.XPATH, "//a[contains(@aria-label, 'Nästa')]"),
            "Bing result links (a[href^='http'])": (By.CSS_SELECTOR, "li.b_algo a[href^='http'], li.b_algo_group a[href^='http']")
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
            "b_algo (li.b_algo) b_algo_group (li.b_algo_group)",
            "h2->a (li > h2 > a)",
            "tilk (a.tilk)",
            "tilk.tptt (a.tilk div.tptt)",
            "Fallback a (li.b_algo a)",
            "Description (p.b_lineclamp*)",
            "Next page (title=Nächste Seite)",
            "Next page (class)",
            "Next page (aria-label=Nächste)",
            "Bing result links (a[href^='http'])"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_bing_se()
    print("Test completed!")
