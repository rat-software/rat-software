import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Dummy-Objekt für HTML- und Screenshot-Mock
class DummyScraping:
    def encode_code(self, html): return "dummy_html_code"
    def take_screenshot(self, driver): return b"dummy_screenshot"

scraping = DummyScraping()

def get_search_results(driver, page):
    results = []
    source = driver.page_source
    soup = BeautifulSoup(source, "lxml")

    serp_code = scraping.encode_code(source)
    serp_bin = scraping.take_screenshot(driver)

    # Suche nach Containern mit Klasse "opt--t-xxs"
    containers = soup.find_all("article", class_=lambda x: x and "O9Ipab51rBntYb0pwOQn IRZ2AvVTFIqv1bxANKqq uhCDl7LxwXLfisVWNgw1" in x)
    print(f"[INFO] {len(containers)} Ergebnisse mit Klasse 'opt--t-xxs' gefunden.")

    for idx, result in enumerate(containers):
        print(f"\n--- Ergebnis #{idx + 1} ---")
        try:
            result_title = result.find('h2')['title']
            print(f"[OK] Titel: {result_title}")
        except:
            result_title = "N/A"
            print("[WARN] Titel nicht gefunden.")

        try:
            footer_div = result.find('div', class_='LJPgIPz9wDJEQlUjokYA vZ_SLtUtIm2HRLmuoqoH _TGhKe0I_bkipHyx1jkc g4l1w73IkDmKIN7qo7G5 Qbym0Y5Mm3IUK2cEH3ha')
            result_description = ' '.join(footer_div.stripped_strings)
            print(f"[OK] Beschreibung: {result_description}")
        except:
            result_description = "N/A"
            print("[WARN] Beschreibung nicht gefunden.")

        try:
            result_url = result.parent['href']
            print(f"[OK] URL: {result_url}")
        except:
            result_url = "N/A"
            print("[WARN] URL nicht gefunden.")

        if result_url != "N/A" and "http" in result_url:
            results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

    return results

# Selenium Webdriver Setup
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Nur aktivieren, wenn du keinen Browser sehen willst
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)
driver.implicitly_wait(10)

try:
    driver.get("https://duckduckgo.com/?q=ki&t=h_&iar=videos&iax=videos&ia=videos")
    time.sleep(2)

    search = driver.find_element(By.NAME, "q")
    search.clear()
    search.send_keys("künstliche intelligenz")
    search.send_keys(Keys.RETURN)

    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    # Ergebnisse extrahieren
    results = get_search_results(driver, page=1)

    # Export in CSV
    with open("ddg_video_results.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Titel", "Beschreibung", "URL", "SERP_Code", "Screenshot", "Seite"])
        writer.writerows(results)

    print(f"\n[INFO] {len(results)} Ergebnisse gespeichert in 'ddg_video_results.csv'.")

finally:
    driver.quit()
