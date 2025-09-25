import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from bs4 import BeautifulSoup
import time

class DummyScraping:
    def encode_code(self, html): return "dummy_html_code"
    def take_screenshot(self, driver): return b"dummy_screenshot"

scraping = DummyScraping()

def get_search_results(driver, page):
    results = []
    source = driver.page_source
    serp_code = scraping.encode_code(source)
    serp_bin = scraping.take_screenshot(driver)

    soup = BeautifulSoup(source, "lxml")


    # Prüfe: Gibt es divs mit Klasse 'mc_fgvc_u'?
    containers = soup.find_all("div", class_="mc_vtvc_meta")
    print(f"Anzahl der Ergebnisse-Container (mc_vtvc_meta): {len(containers)}")

    for idx, result in enumerate(containers):
        print(f"\n== Ergebnis #{idx+1} ==")

        # Prüfe Titel-Container
        div_title = result.find('div', class_='mc_vtvc_title')
        if div_title:
            print("Gefunden: div.mc_vtvc_title mit title =", div_title.get('title'))
            title = div_title.get('title')
        else:
            print("Kein div.mc_vtvc_title gefunden")
            title = "N/A"

        # Prüfe Meta-Block
        meta_block = result.find('div', class_='mc_vtvc_meta_block_area')
        if meta_block:
            print("Gefunden: div.mc_vtvc_meta_block_area")
            texts = []
            try:
                views = meta_block.find('span', class_='meta_vc_content').text
                print(" - meta_vc_content:", views)
                texts.append(views)
            except:
                print(" - meta_vc_content nicht gefunden")
            try:
                date = meta_block.find('span', class_='meta_pd_content').text
                print(" - meta_pd_content:", date)
                texts.append(date)
            except:
                print(" - meta_pd_content nicht gefunden")
            try:
                span2 = meta_block.find_all('span')[2].text
                print(" - drittes span:", span2)
                texts.append(span2)
            except:
                print(" - drittes span nicht gefunden")
            try:
                channel = meta_block.find('span', class_='mc_vtvc_meta_row_channel').text
                print(" - channel:", channel)
                texts.append(channel)
            except:
                print(" - channel nicht gefunden")
            description = ' '.join(texts)
        else:
            print("Kein div.mc_vtvc_meta_block_area gefunden")
            description = "N/A"

        # Prüfe URL-Container
        div_url = result.find('div', class_='mc_vtvc_con_rc')
        if div_url:
            ourl = div_url.get('ourl')
            print("Gefunden: div.mc_vtvc_con_rc mit ourl =", ourl)
            url = ourl if ourl else "N/A"
        else:
            print("Kein div.mc_vtvc_con_rc gefunden")
            url = "N/A"

        if url != "N/A" and "http" in url:
            results.append([title, description, url, serp_code, serp_bin, page])

    return results

# Setup WebDriver
options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # Optional: Browser nicht sichtbar
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)
driver.implicitly_wait(10)

try:
    # Seite öffnen und Suche ausführen
    driver.get("https://www.bing.com/?scope=video&nr=1&?cc=de&setLang=de")
    time.sleep(1)
    search = driver.find_element(By.NAME, "q")
    search.send_keys("künstliche intelligenz")
    search.send_keys(Keys.RETURN)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Ergebnisse holen
    results = get_search_results(driver, page=1)

    # Ergebnisse in CSV schreiben
    with open("bing_video_results.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Header
        writer.writerow(["Titel", "Beschreibung", "URL", "Serp_Code", "Serp_Bin", "Seite"])
        # Daten
        for row in results:
            writer.writerow(row)

    print(f"✅ {len(results)} Ergebnisse wurden in 'bing_video_results.csv' gespeichert.")

finally:
    driver.quit()
