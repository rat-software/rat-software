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
def test_bing_video_nl():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="nl"
    )
    driver.set_page_load_timeout(30)

    try:
        driver.get("https://www.bing.com/?scope=video&nr=1&?cc=nl&setLang=nl")

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
            wait.until(EC.presence_of_element_located((By.ID, "vsb_vid_cat")))
            results_elements = driver.find_elements(By.ID, "vsb_vid_cat")
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: 'vsb_vid_cat' not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")

        # Check for key result DOM elements with debug output   
        selectors = {
            "Result container (div.mc_vtvc_meta)": (By.CSS_SELECTOR, "div.mc_vtvc_meta"),
            "Title div (div.mc_vtvc_title)": (By.CSS_SELECTOR, "div.mc_vtvc_title"),
            "Meta block (div.mc_vtvc_meta_block_area)": (By.CSS_SELECTOR, "div.mc_vtvc_meta_block_area"),
            "Views (span.meta_vc_content)": (By.CSS_SELECTOR, "div.mc_vtvc_meta_block_area span.meta_vc_content"),
            "Date (span.meta_pd_content)": (By.CSS_SELECTOR, "div.mc_vtvc_meta_block_area span.meta_pd_content"),
            "Meta block spans": (By.CSS_SELECTOR, "div.mc_vtvc_meta_block_area span"),
            "Channel (span.mc_vtvc_meta_row_channel)": (By.CSS_SELECTOR, "div.mc_vtvc_meta_block_area span.mc_vtvc_meta_row_channel"),
            "URL container (div.mc_vtvc_con_rc)": (By.CSS_SELECTOR, "div.mc_vtvc_con_rc"),
            "Next page (class)": (By.CSS_SELECTOR, "a.sb_pagN, a.sb_pagN_bp, a.b_widePag, a.sb_bp"),
            "div.mc_vtvc_con_rc with ourl": (By.XPATH, "//div[contains(@class, 'mc_vtvc_con_rc') and @ourl]")
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
            "Result container (div.mc_vtvc_meta)",
            "Title div (div.mc_vtvc_title)",
            "Meta block (div.mc_vtvc_meta_block_area)",
            "Views (span.meta_vc_content)",
            "Date (span.meta_pd_content)",
            "Meta block spans",
            "Channel (span.mc_vtvc_meta_row_channel)",
            "URL container (div.mc_vtvc_con_rc)",
            "Next page (class)",
            "div.mc_vtvc_con_rc with ourl"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_bing_video_nl()
    print("Test completed!")
