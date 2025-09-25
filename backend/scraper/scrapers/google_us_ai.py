import csv
import os
import inspect
from pathlib import Path
import random
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import html2text
import markdown
import re


def accept_cookie(driver):
    """
    Klickt auf den Cookie-Zustimmungs-Button, falls vorhanden.
    """
    try:
        wait = WebDriverWait(driver, 10)
        cookie_accept_button = wait.until(
            EC.element_to_be_clickable((By.ID, "L2AGLb"))
        )
        cookie_accept_button.click()
        print("Cookie banner accepted.")
    except TimeoutException:
        print("No cookie banner found or timeout reached.")
    except Exception as e:
        print(f"Error clicking cookie banner: {e}")

def extract_all_current_sources(soup_obj):
    """
    Hilfsfunktion, um alle Quelleninformationen (Titel, Beschreibung, Link)
    aus den LLtSOc-Listenelementen innerhalb eines BeautifulSoup-Objekts zu extrahieren.
    """
    current_sources = []
    for div_item in soup_obj.find_all("div", class_="mv7LYc"):
        for li_item in div_item.find_all("li", class_="LLtSOc"):
            title_div = li_item.find("div", class_="mNme1d tNxQIb")
            title = title_div.get_text(strip=True) if title_div else ""

            description_div = li_item.find("div", class_="ZigeC wHYlTd")
            description = description_div.get_text(strip=True) if description_div else ""

            kevend_link = li_item.find("a", class_="KEVENd")
            href = kevend_link.get("href", "").strip() if kevend_link else ""
            
            if href:
                source_entry = {
                    "title": title,
                    "description": description,
                    "href": href
                }
                if kevend_link:
                    link_aria_label = kevend_link.get("aria-label", "").strip()
                    if link_aria_label and link_aria_label != title:
                        source_entry["link_aria_label"] = link_aria_label
                
                current_sources.append(source_entry)
    return current_sources

def check_captcha(driver):
    """
    Überprüft, ob ein CAPTCHA auf der Seite vorhanden ist.
    """
    return "g-recaptcha" in driver.page_source

def format_answer(ai_container):
    """
    Formatiert den Text aus dem AI Overview-Container.
    """
    ai_overview_text, ai_overview_text_html = "", ""
    ai_overview_html = ai_container.get_attribute('innerHTML')

    filter_text = ["Opens in new tab", "View all"]
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.body_width = 0 
    plain_text = h.handle(ai_overview_html)

    lines = plain_text.split('\n')
    cleaned_lines = [
        line for line in lines 
        if not any(keyword in line for keyword in filter_text)
    ]
    cleaned_text = '\n'.join(cleaned_lines)
    final_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    final_text = final_text.strip()
    
    ai_overview_text = final_text
    ai_overview_text_html = markdown.markdown(final_text)

    return ai_overview_text, ai_overview_text_html

def run(query, limit, scraping, headless):
    """
    Führt eine Google-Suche durch und extrahiert den AI Overview.
    """
    driver = None
    ai_overview_text = None
    ai_overview_text_html = None
    sources = [] 

    try:
        proxies = []
        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        proxy_file_path = os.path.join(currentdir, 'proxies', 'Germany.csv')
        if os.path.exists(proxy_file_path):
            with open(proxy_file_path) as csvfile:
                csv_reader = csv.reader(csvfile, delimiter=',')
                for row in csv_reader:
                    proxies.append(row)
        else:
            print(f"Warning: Proxy file not found at {proxy_file_path}. Proceeding without proxies.")

        random.shuffle(proxies)
        proxy = proxies[0][0] if proxies else None

        search_url = "https://www.google.com/webhp?hl=en&gl=US&uule=w+CAIQICImV2VzdCBOZXcgWW9yayxOZXcgSmVyc2V5LFVuaXRlZCBTdGF0ZXM%3D" 
        search_box = "q"
        
        driver = Driver(
            browser="chrome", wire=True, uc=True, headless2=headless, incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            do_not_track=True, undetectable=True, locale_code="en-US"
        )

        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10) # Reduziert, um nicht zu lange zu warten
        driver.get(search_url)
        accept_cookie(driver)
        time.sleep(random.randint(1, 2))

        if check_captcha(driver):
            print("CAPTCHA detected.")
            return -1
        
        search = driver.find_element(By.NAME, search_box)
        search.send_keys(query)
        search.send_keys(Keys.RETURN)
        time.sleep(random.randint(1, 2))

        # Versuch, den "Show more answers" Button zu klicken
        try:
            more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "SlP8xc"))
            )
            driver.execute_script("arguments[0].click();", more_button)
            print("'Show more answers' button clicked.")
            time.sleep(2) 
        except Exception:
            print("No 'Show more answers' button found or not clickable.")
        
        ai_container = None
        try:
            # Versuch, den primären und sekundären Container in einem Block zu finden
            ai_container = driver.find_element(By.CSS_SELECTOR, "div.LT6XE")
            print("AI Overview element found.")
            ai_overview_text, ai_overview_text_html = format_answer(ai_container)

            # Versuch, den "More Sources" Button zu klicken
            try:
                more_sources_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.NiIRyf"))
                )
                driver.execute_script("arguments[0].click();", more_sources_button)
                print("A 'More Sources' button (NiIRyf) was found and will be clicked.")
                time.sleep(2)
            except (TimeoutException, NoSuchElementException):
                print("No 'More Sources' button (NiIRyf) found.")
            
            soup = BeautifulSoup(driver.page_source, features="lxml")
            sources = extract_all_current_sources(soup)
        except NoSuchElementException:
            print("No AI Overview element found after search.")
            return -1

        # Gibt die gesammelten Daten zurück
        return ai_overview_text, ai_overview_text_html, sources

    except Exception as e:
        print(f"Fatal error: {e}")
        return -1

    finally:
        # Sorgt dafür, dass der Browser immer geschlossen wird, egal was passiert
        if driver:
            driver.quit()

if __name__ == "__main__":
    query = "what is diabetes"
    headless = False
    limit = 1
    scraping = False
    answers = run(query, limit, scraping, headless)

    if answers == -1:
        print("Test run failed.")

    else:
    
        if answers and answers[0] is not None:
            print("\n--- AI Overview Text ---")
            print(answers[0])
            print("\n--- AI Overview HTML ---")
            print(answers[1])
            # print("\n--- Associated Sources ---")
            # print(json.dumps(answers[2], indent=4))
        else:
            print("\nFailed to retrieve AI Overview.")