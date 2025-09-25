import os
import random
import time
import json
from seleniumbase import Driver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

import markdown
import html2text
from bs4 import BeautifulSoup


def accept_cookie(driver):
    try:
        cookie_accept_button = driver.find_element(By.CLASS_NAME, "fzpdr32RS4bbAHfe8pJj")
        cookie_accept_button.click()
        print("Cookie banner accepted.")
        time.sleep(random.uniform(0.5, 1.5))
    except TimeoutException:
        print("No cookie banner found or timeout reached.")
    except Exception as e:
        print(f"Error clicking cookie banner: {e}")


# Helper-Funktionen bleiben unverändert
def dismiss_popups(driver):
    popup_selectors = [
        "button[data-testid='dismiss-welcome']",
        "button[data-testid='close-button']"
    ]
    for selector in popup_selectors:
        try:
            driver.click(selector, timeout=3)
            print(f"Pop-up mit Selektor '{selector}' wurde geschlossen.")
            time.sleep(random.uniform(0.5, 1.5))
            return
        except Exception:
            continue
    print("Keine bekannten Pop-ups gefunden.")

def format_answer(ai_container_tag):
    source_html = str(ai_container_tag)
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    markdown_text = h.handle(source_html).strip()
    return markdown_text, source_html

def run(query, limit, scraping, headless):
    driver = None
    try:
        driver = Driver(
            browser="chrome", uc=True, headless2=headless, incognito=True,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            do_not_track=True, undetectable=True, locale_code="en-US", no_sandbox=True
        )
        
        driver.get("https://chatgpt.com/")
        time.sleep(random.uniform(3.0, 5.0))
        #accept_cookie(driver)
        time.sleep(random.uniform(1.0, 2.0))
        dismiss_popups(driver)

        # Schritt 1: Anfrage senden
        search_box_selector = '#prompt-textarea'
        try:
            driver.wait_for_element_visible(search_box_selector, timeout=20)
            print("Text-Eingabefeld ist sichtbar.")
            driver.type(search_box_selector, query + "\n", timeout=10)
            print(f"Anfrage '{query}' wurde gesendet. Warte auf Antwort...")
        except (TimeoutException, Exception) as e:
            print(f"Fehler beim Senden der Anfrage: {e}")
            return -1

        # Schritt 2: Warten auf die Antwort (TEST MIT FESTER WARTEZEIT)
        # Wir ersetzen die dynamische Wartezeit durch eine feste Pause.
        # Dies ist nicht ideal für die Geschwindigkeit, aber ein sehr guter Test,
        # um komplexe Lade- oder Bot-Schutz-Probleme zu umgehen.
        wait_time = 30
        print(f"Warte {wait_time} Sekunden, damit die Antwort vollständig laden kann...")
        time.sleep(wait_time)
        print("Wartezeit beendet. Versuche, die Antwort zu extrahieren.")

        # Schritt 3: Daten sichern und extrahieren
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "lxml")

        ai_container_selector = "div.markdown.prose"
        ai_containers = soup.select(ai_container_selector)
        
        if ai_containers:
            ai_container_tag = ai_containers[-1]
            print(f"{len(ai_containers)} Antwort-Container im HTML gefunden. Der letzte wird verwendet.")
            ai_overview_text, ai_overview_html = format_answer(ai_container_tag)
            sources = []
            return ai_overview_text, ai_overview_html, sources
        else:
            print("Keinen finalen Antwort-Container im HTML gefunden.")
            # Optional: Speichere den HTML-Code zur Analyse, wenn nichts gefunden wird
            # with open("debug_page_source.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            # print("HTML-Quelltext wurde in 'debug_page_source.html' gespeichert.")
            return -1

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

# ### Test Block ###
if __name__ == "__main__":
    test_query = "what is migraine?"
    result = run(query=test_query, limit=1, scraping=None, headless=True)

    if result == -1:
        print("\nTestlauf fehlgeschlagen.")
    else:
        ai_text, ai_html, sources = result
        print("\n--- AI Übersicht (formatiertes Markdown) ---")
        print(ai_text)
        print(ai_html)