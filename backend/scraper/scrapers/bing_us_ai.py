import csv
import os
import inspect
import random
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import html2text
import markdown
import re

# ############################################################# #
# ### START: HELPER FUNCTIONS (Angepasst an google_de_ai.py) ### #
# ############################################################# #

def accept_cookie(driver):
    """
    Klickt auf den Cookie-Zustimmungs-Button, falls vorhanden.
    Verwendet einen JavaScript-Klick, um Blockaden (Intercepts) zu umgehen.
    """
    try:
        # Warte, bis der Button im Code der Seite vorhanden ist (10s max)
        cookie_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "bnp_btn_accept"))
        )
        
        # Führe einen Klick per JavaScript aus, der zuverlässiger ist
        driver.execute_script("arguments[0].click();", cookie_button)
        
        print("Cookie-Banner akzeptiert.")
        time.sleep(random.uniform(0.5, 1.5))
    except TimeoutException:
        print("Kein Cookie-Banner gefunden oder nicht klickbar.")
    except Exception as e:
        print(f"Fehler beim Schließen des Cookie-Banners: {e}")

def extract_all_current_sources(soup_obj, driver):
    """
    Extrahiert alle Quelleninformationen aus dem AI-Übersichtsbereich von Bing.
    """
    current_sources = []
    # Der Hauptcontainer für Quellen bei Bing
    main_div = soup_obj.find("div", class_="hov hov-anime h_def")
    
    if main_div:
        # Finde alle a-Tags, die einzelne Quellen repräsentieren
        for link_item in main_div.find_all("a", class_="hov-item"):
            href = link_item.get('href', '').strip()

            try:
                driver.get(href)
                time.sleep(4)
                href = driver.current_url #read real url (redirected url)
            except Exception as e:
                print(str(e))
                pass

            title_div = link_item.find("div", class_="hov-item-ttl")
            title = title_div.get_text(strip=True) if title_div else "N/A"
            
            description_div = link_item.find("div", class_="hov-item-snip")
            description = description_div.get_text(strip=True) if description_div else "N/A"
            
            if href:
                source_entry = {
                    "title": title,
                    "description": description,
                    "href": href
                }
                current_sources.append(source_entry)
    return current_sources

def check_captcha(driver):
    """
    Überprüft, ob ein CAPTCHA auf der Seite vorhanden ist.
    """
    return "g-recaptcha" in driver.page_source

def format_answer(ai_container):
    """
    Extrahiert und formatiert den Text aus dem AI-Container von Bing.
    Filtert unerwünschte Elemente wie "Bilder", "Videos" am Anfang
    und URLs am Ende des Textes.
    """
    # 1. Rohtext aus dem Web-Element extrahieren
    plain_text = ai_container.text

    # 2. Alles ab der ersten "www."-URL am Ende abschneiden
    url_start_index = plain_text.find("www.")
    if url_start_index != -1:
        plain_text = plain_text[:url_start_index]

    # 3. "Bilder" und "Videos" am Anfang entfernen
    #    Dies entfernt alle Kombinationen wie "Bilder", "Videos", "Bilder Videos", etc.
    #    und jeglichen Leerraum (Zeilenumbrüche) danach.
    cleaned_text = re.sub(r'^(Bilder\s*|Videos\s*)+', '', plain_text.strip())

    # 4. Führende/nachfolgende Leerzeichen vom finalen Text entfernen
    final_text = cleaned_text.strip()

    # 5. Eine HTML-Version erstellen und beides zurückgeben
    html_text = markdown.markdown(final_text)
    return final_text, html_text

def run(query, limit, scraping, headless):
    """
    Führt eine Bing-Suche durch und extrahiert den AI Overview.
    Die Struktur und der Rückgabewert sind an google_de_ai.py angelehnt.
    """
    driver = None
    try:
        # Proxy-Logik (identisch zu google_de_ai.py)
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

        # Konstanten
        language_url = "https://www.bing.com/?cc=US&setLang=en"
        search_box_name = "q"
        
        # WebDriver-Initialisierung
        driver = Driver(
            browser="chrome", wire=True, uc=True, headless2=headless, incognito=False,
            agent="Mozilla/G/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            do_not_track=True, undetectable=True, locale_code="en-US"
        )
        driver.set_page_load_timeout(60)

        # Scraping-Logik
        driver.get(language_url)
        accept_cookie(driver)
        time.sleep(random.uniform(1.0, 2.0))

        if check_captcha(driver):
            print("CAPTCHA erkannt.")
            return -1

        search_input = driver.find_element(By.NAME, search_box_name)
        search_input.send_keys(query)
        search_input.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2.5, 4.5))

        # AI-Übersicht Extraktion
        ai_container = None
        try:
            # Warten, bis der Container für die KI-Übersicht sichtbar ist
            ai_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.gs_h.gs_caphead"))
            )
            print("AI-Übersicht-Container gefunden.")
        except (NoSuchElementException, TimeoutException):
            print("Kein AI-Übersicht-Element auf der Seite gefunden.")
            return -1 # Rückgabe -1, wenn kein Container gefunden wird

        if ai_container:
            ai_overview_text, ai_overview_html = format_answer(ai_container)

            # Klicke auf "Mehr Quellen", falls vorhanden
            try:
                more_sources_button = driver.find_element(By.CLASS_NAME, "gs_readMoreFullBtn")
                driver.execute_script("arguments[0].click();", more_sources_button)
                print("'Mehr Quellen'-Button geklickt.")
                time.sleep(2)
            except (NoSuchElementException, TimeoutException):
                print("Kein 'Mehr Quellen'-Button gefunden.")
            
            # Extrahiere die Quellen
            soup = BeautifulSoup(driver.page_source, "lxml")
            sources = extract_all_current_sources(soup, driver)
            
            # Rückgabe im Tupel-Format (text, html, quellen)
            return ai_overview_text, ai_overview_html, sources

    except Exception as e:
        print(f"Ein schwerwiegender Fehler ist aufgetreten: {str(e)}")
        import traceback
        traceback.print_exc()
        return -1

    finally:
        if driver:
            try:
                driver.quit()
                print("WebDriver wurde geschlossen.")
            except Exception as e:
                print(f"Fehler beim Schließen des WebDrivers: {e}")


# ############################################################# #
# ### START: TEST BLOCK (identisch zu google_de_ai.py)      ### #
# ############################################################# #

if __name__ == "__main__":
    test_query = "what is migraine?"
    # Setze headless auf False, um den Browser zu sehen
    result = run(query=test_query, limit=1, scraping=None, headless=True)

    if result == -1:
        print("Testlauf fehlgeschlagen.")
    elif not result:
        print("Keine AI-Übersicht gefunden.")
    else:
        ai_text, ai_html, ai_sources = result
        print("\n--- AI Übersicht Text ---")
        print(ai_text)
        print("\n--- AI Übersicht HTML ---")
        print(ai_html)
        print("\n--- Zugehörige Quellen ---")
        print(json.dumps(ai_sources, indent=2, ensure_ascii=False))
# ############################################################# #
# ### ENDE: TEST BLOCK                                      ### #
# ############################################################# #