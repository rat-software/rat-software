# Erforderliche zusätzliche Importe
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Deine bestehenden Importe
from scrapers.requirements import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import random

# Helferfunktion, um die Region auf der Ergebnisseite (SERP) zu setzen
def set_region_on_serp(driver, wait): 
    """
    Sucht den Regionen-Umschalter auf der Suchergebnisseite (SERP) und stellt ihn auf 'United States'.
    """
    region_code = "de-de"        
    region_label = "Deutschland"
    try:
        print("INFO: Suche den 'Search region:' Button auf der Ergebnisseite...")
        
        # 1. Finde und klicke den Button, der das Dropdown-Menü öffnet, anhand seines Textes.
        region_button_selector = (By.XPATH, "//button[.//span[contains(text(), 'Suchgebiet:')]]")
        region_button = wait.until(EC.element_to_be_clickable(region_button_selector))
        driver.execute_script("arguments[0].click();", region_button)
        print("INFO: Regionen-Dropdown wurde geöffnet.")
        
        # 2. Finde und klicke die "United States"-Option in der nun sichtbaren Liste.
        #    Wir verwenden die exakte 'data-test-id' aus deinem HTML-Fund.
        us_option_selector = (By.CSS_SELECTOR, f"li[data-test-id='search-regions-region-{region_code}']")
        us_option = wait.until(EC.element_to_be_clickable(us_option_selector))
        
        print(f"INFO: Regionsoption '{region_label}' gefunden. Klicke...")
        us_option.click()
        
        print(f"SUCCESS: Region '{region_label}' wurde ausgewählt.")
        
        # 3. LANGE PAUSE ZUM BEOBACHTEN
        print("INFO: Starte 5-sekündige Pause zum Beobachten...")
        time.sleep(5)
        print("INFO: Pause beendet.")
        
        return True
        
    except Exception as e:
        print(f"WARNUNG: Region konnte auf dieser Seite nicht geändert werden. Mache mit der Standardsuche weiter. Fehler: {e}")
        return False


def run(query, limit, scraping, headless):
    """
    Führt den Ecosia EN Scraper aus.
    """
    driver = None
    try:
        # ======================================================================
        # 1. TREIBER INITIALISIEREN
        # ======================================================================
        driver = Driver(
            browser="chrome", wire=True, uc=True, headless2=headless, incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            do_not_track=True, undetectable=True, locale_code="de-DE"
        )
        wait = WebDriverWait(driver, 15)
        driver.maximize_window()
        driver.get("https://www.ecosia.org/")

        # Cookie-Banner behandeln
        try:
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            driver.execute_script("arguments[0].click();", accept_button)
        except Exception:
            print("INFO: Cookie-Banner nicht gefunden.")

        # ======================================================================
        # 2. INTERNE FUNKTIONEN (DEIN BESTEHENDER CODE)
        # ======================================================================
        captcha = "g-recaptcha"
        search_box_name = "q"

        def get_search_results(driver, page):
            temp_search_results = []
            source = driver.page_source
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, "lxml")
            for result in soup.select('div.result--web, article.card-web, div.result__body'):
                result_title, result_description, result_url = "N/A", "N/A", "N/A"
                try:
                    title_elem = result.select_one('a.result-title, h2 a, div.result__title')
                    if title_elem: result_title = title_elem.get_text(strip=True)
                except: pass
                try:
                    desc_elem = result.select_one('p.result-snippet, div.result-snippet, div.result__description')
                    if desc_elem: result_description = desc_elem.get_text(strip=True)
                except: pass
                try:
                    url_elem = result.select_one('a.result-title, a.result-url, h2 a, a.result__link')
                    if url_elem: result_url = url_elem.get('href')
                except: pass
                if result_url != "N/A":
                    temp_search_results.append([result_title, result_description, result_url, serp_code, serp_bin, page])
            return temp_search_results

        def check_captcha(driver):
            return captcha in driver.page_source

        def remove_duplicates(search_results):
            seen_urls = set()
            unique_results = []
            for result in search_results:
                url = result[2]
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            return unique_results

        # ======================================================================
        # 3. SUCHE STARTEN UND DATEN SAMMELN
        # ======================================================================
        search_results = []
        page = 0
        
        print(f"Führe die Suche nach '{query}' aus...")
        search_box_element = wait.until(EC.element_to_be_clickable((By.NAME, search_box_name)))
        search_box_element.clear()
        search_box_element.send_keys(query)
        search_box_element.send_keys(Keys.RETURN)
        
        wait.until(EC.presence_of_element_located((By.ID, "main")))

        # ERSTER AUFRUF der Regionen-Funktion
        set_region_on_serp(driver, wait)
        
        if check_captcha(driver):
            print("FEHLER: Captcha gefunden. Breche ab.")
            return -1
        
        search_results.extend(get_search_results(driver, page))

        # Paginierungsschleife
        while len(search_results) < limit:
            page += 1
            print(f"Navigiere zu Ergebnisseite {page}...")
            
            try:
                next_page_url = f"https://www.ecosia.org/search?q={query}&p={page}"
                driver.get(next_page_url)
                
                # WIEDERHOLTER AUFRUF der Regionen-Funktion auf jeder neuen Seite
                set_region_on_serp(driver, wait)

                if check_captcha(driver):
                    print("FEHLER: Captcha auf Folgeseite gefunden. Beende das Scraping.")
                    break

                new_results = get_search_results(driver, page)
                if not new_results:
                    print("INFO: Keine weiteren Ergebnisse gefunden.")
                    break
                
                search_results.extend(new_results)
                search_results = remove_duplicates(search_results)
                print(f"INFO: Bisher {len(search_results)} einzigartige Ergebnisse gesammelt.")

            except Exception as e:
                print(f"FEHLER beim Laden der nächsten Seite: {e}")
                break

        print(f"INFO: Scraping beendet. {len(search_results)} einzigartige Ergebnisse gefunden.")
        return search_results[:limit]

    except Exception as e:
        print(f"FEHLER im Hauptprozess: {e}")
        return -1

    finally:
        if driver:
            print("INFO: Schließe den WebDriver.")
            driver.quit()