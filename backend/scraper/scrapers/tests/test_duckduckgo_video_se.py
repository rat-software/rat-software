import time
import sys
import os
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scrapers.requirements import *

@pytest.mark.selenium
def test_duckduckgo_video_se():
    driver = Driver(
    browser="chrome", wire=True, uc=True, headless2=True, incognito=False,
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    do_not_track=True, undetectable=True, locale_code="sv-SE"
    )
    driver.set_page_load_timeout(30)

    try:
        results = {}
        
        # 1. Set language and region, then verify language setting
        try:
            print("\nLanguage and region: Opening settings page …")
            driver.get("https://duckduckgo.com/settings/")
            wait = WebDriverWait(driver, 10)

            # Set region
            try:
                region_dropdown = wait.until(EC.presence_of_element_located(
                    (By.ID, "setting_kl")))
                select = Select(region_dropdown)
                select.select_by_value("se-sv")
                print("Region set to 'se-sv'.")
                results["Region setting applied(se-sv)"] = True
            except Exception as e:
                print(f"Failed to set region: {e}")
                results["Region setting applied (se-sv)"] = False

            # Set language
            try:
                language_dropdown = wait.until(EC.presence_of_element_located((By.ID, "setting_kad")))
                Select(language_dropdown).select_by_value("sv_SE")
                print("Language set to 'sv_SE'.")
                results["Language setting applied (sv_SE)"] = True
            except Exception as e:
                print(f"Failed to set language: {e}")
                results["Language setting applied (sv_SE)"] = False


            # Return to main page and check <html lang="...">
            driver.get("https://duckduckgo.com/")
            time.sleep(2)
            html_tag = driver.find_element(By.TAG_NAME, "html")
            page_lang = html_tag.get_attribute("lang")
            print(f"Detected page language: {page_lang}")
            if page_lang and page_lang == "sv-SE":
                print("Language setting successfully applied (via lang attribute).")
                results["Language setting confirmed"] = True
            else:
                print("Language setting not applied.")
                results["Language setting confirmed"] = False
        except Exception as e:
            print(f"Error during language/region setting: {e}")
            results["Region setting applied (se-sv)"] = False
            results["Language setting applied (sv_SE)"] = False
            results["Language setting confirmed"] = False


        # 2. Check for CAPTCHA immediately after loading the page
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

        # 3. Accept cookie banner (if present)
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

        # 4. Locate search box and perform a search
        try:
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys("test" + Keys.RETURN)
            results["Search box (By.NAME = 'q')"] = True
        except NoSuchElementException:
            results["Search box (By.NAME = 'q')"] = False
            print("Search box not found!")

         # 5. Switch to video tab (after search)
        try:
            print("\nSwitching to video tab ...")
            wait = WebDriverWait(driver, 10)
            video_tab = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href, 'ia=videos') and contains(@href, 'iax=videos')]")
            ))
            video_tab.click()
            time.sleep(2)  # Give time for the page to transition
            print("Switched to video tab.")
            results["Video tab opened"] = True
        except TimeoutException:
            print("Video tab not found or not clickable.")
            results["Video tab opened"] = False
        except Exception as e:
            print(f"Error switching to video tab: {e}")
            results["Video tab opened"] = False

        # 6. Wait for search results to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="result"]')))
            results_elements = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="result"]')
            assert len(results_elements) > 0, "No search results found on result page."
        except TimeoutException:
            raise AssertionError("Timeout: DuckDuckGo video results not found in DOM.")
        except Exception as e:
            raise AssertionError(f"Error accessing result elements: {e}")

        # 7. Check for key result DOM elements with debug output
        selectors = {
            "Result container (article.O9Ipab...)": (By.CSS_SELECTOR, "article.O9Ipab51rBntYb0pwOQn.IRZ2AvVTFIqv1bxANKqq.uhCDl7LxwXLfisVWNgw1"),
            "Title (h2 with 'title' attribute)": (By.CSS_SELECTOR, "article.O9Ipab51rBntYb0pwOQn.IRZ2AvVTFIqv1bxANKqq.uhCDl7LxwXLfisVWNgw1 h2[title]"),
            "Description (div.LJPgIPz9...)": (By.CSS_SELECTOR, "div.LJPgIPz9wDJEQlUjokYA.vZ_SLtUtIm2HRLmuoqoH._TGhKe0I_bkipHyx1jkc.g4l1w73IkDmKIN7qo7G5.Qbym0Y5Mm3IUK2cEH3ha"),
            "Link (parent <a> of article)": (By.XPATH, "//article[contains(@class, 'O9Ipab')]/parent::*[self::a and @href]"),
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
            "Result container (article.O9Ipab...)",
            "Title (h2 with 'title' attribute)",
            "Description (div.LJPgIPz9...)",
            "Link (parent <a> of article)"
        ]
        for elem in required_elements:
            assert results.get(elem), f"Expected element '{elem}' was not found."
            
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_duckduckgo_video_se()
    print("Test completed!")
    
