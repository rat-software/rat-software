from scrapers.requirements import *

def run(query, limit, scraping, headless):
    """
    Scrapes Bing search results in French.

    Args:
        query (str): The search query.
        limit (int): Maximum number of search results to retrieve.
        scraping: The Scraping object used for encoding and taking screenshots.
        headless (bool): If True, run the browser in headless mode.

    Returns:
        list: A list of search results, where each result is a list [title, description, url, serp_code, serp_bin, page].
              Returns -1 if CAPTCHA is detected or an error occurs.

        language_url = "https://www.bing.com/?cc=fr&setLang=fr"
        locale = "fr"
        next_page = "Page suivante"
    """    
    driver = None  # Initialisiere driver hier, um ihn im finally-Block sicher schließen zu können
    try:
        # Define constants
        language_url = "https://www.bing.com/?cc=fr&setLang=fr"  # Bing German homepage
        locale = "fr"
        next_page = "Page suivante"
        base_url = "https://www.bing.com" # Basis-URL für relative Links
        captcha_marker = "g-recaptcha"  # Indicator for CAPTCHA
        # Initialize variables
        page = 1
        search_results = []
        results_number = 0
        search_box = "q"  # Name attribute of the search box input field

        def get_search_results(driver_instance, current_page):
            """
            Extracts search results from the current page.
            (Funktion bleibt im Wesentlichen gleich, nur der Name des Driver-Parameters geändert zur Klarheit)
            """
            results = []
            source = driver_instance.page_source

            # Encode page source and capture a screenshot
            # Diese sollten nur einmal pro Seite gemacht werden, nicht pro Ergebnis
            serp_code_page = scraping.encode_code(source)
            serp_bin_page = scraping.take_screenshot(driver_instance)

            soup = BeautifulSoup(source, "lxml")

            for tag in soup.find_all("span", class_=["algoSlug_icon"]):
                tag.extract()
            for tag in soup.find_all("li", class_=["b_algoBigWiki"]):
                tag.extract()

            for result in soup.find_all("li", class_=["b_algo", "b_algo_group"]):
                try:
                    h2_link = result.find('h2').find('a')
                    if h2_link:
                        title = h2_link.text.strip()
                    else:
                        title_elem = result.find('a', class_='tilk')
                        if title_elem and title_elem.find('div', class_='tptt'):
                            title = title_elem.find('div', class_='tptt').text.strip()
                        else:
                            title_elem_fallback = result.find("a")
                            title = title_elem_fallback.text.strip() if title_elem_fallback else "N/A"
                except Exception as e:
                    # print(f"Error extracting title: {e}") # Optional: Für Debugging aktivieren
                    title = "N/A"
                try:
                    description_elem = result.find("p", class_=lambda x: x and "b_lineclamp" in x)
                    description = description_elem.text.strip() if description_elem else "N/A"
                except:
                    description = "N/A"

                try:
                    url_elem = result.find("a")
                    url = url_elem["href"] if url_elem and url_elem.has_attr("href") else "N/A"
                    url = scraping.decode_bing_url(url)
                except:
                    url = "N/A"
                    
                if url != "N/A" and url.startswith(("http://", "https://")) and not url.startswith("https://bing.com"):
                    results.append([title, description, url, serp_code_page, serp_bin_page, current_page])
            return results

        def check_captcha(driver_instance):
            return captcha_marker in driver_instance.page_source

        def remove_duplicates(results):
            seen_urls = {}
            unique_results = []
            for result_item in results:
                # result_item[2] ist die URL
                if result_item[2] not in seen_urls:
                    unique_results.append(result_item)
                    seen_urls[result_item[2]] = True
            return unique_results

        # Initialize the Selenium WebDriver
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,
            incognito=False,
            do_not_track=True,
            undetectable=True,
            # extension_dir=ext_path, # Stelle sicher, dass ext_path definiert ist, falls verwendet
            locale_code=locale
        )
        driver.maximize_window()
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10) # Implizite Wartezeit kann manchmal helfen, aber explizite Waits sind oft besser

        driver.get(language_url)
        time.sleep(random.uniform(1.5, 3.0))

        search_input = driver.find_element(By.NAME, search_box)
        search_input.send_keys(query)
        search_input.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2.0, 4.0))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scrollen nach der ersten Suche

        try:
            # Versuche, Cookie-Banner zu schließen (Selektor anpassen, falls nötig)
            cookie_button = driver.find_element(By.CLASS_NAME, "bnp_btn_accept")
            cookie_button.click()
            print("Cookie-Banner akzeptiert.")
            time.sleep(random.uniform(0.5, 1.5))
        except TimeoutException:
            print("Kein Cookie-Banner gefunden oder nicht klickbar innerhalb der Zeit.")
        except Exception as e:
            print(f"Fehler beim Schließen des Cookie-Banners: {e}")


        # --- Initialer Abruf der Ergebnisse ---
        if check_captcha(driver):
            print("CAPTCHA auf der ersten Seite erkannt.")
            return -1 # CAPTCHA

        current_results = get_search_results(driver, page)
        if current_results:
            search_results.extend(current_results)
            search_results = remove_duplicates(search_results) # Duplikate nach dem ersten Abruf entfernen
            results_number = len(search_results)
            print(f"Erste Seite: {results_number} Ergebnisse für '{query}' gefunden.")
        else:
            print(f"Keine Ergebnisse auf der ersten Seite für '{query}' gefunden.")
            # Hier könntest du entscheiden, ob du trotzdem weitermachen willst oder abbrichst
            # Fürs Erste gehen wir davon aus, dass es keine Ergebnisse gibt und geben -1 zurück,
            # oder eine leere Liste, je nach gewünschtem Verhalten.
            return [] # Oder -1, wenn das die Konvention für "keine Ergebnisse" ist

        # --- Schleife für weitere Seiten ---
        continue_scraping = True
        if not search_results: # Wenn schon auf der ersten Seite nichts war
            continue_scraping = False

        while results_number < limit and continue_scraping:
            print(f"Aktuelle Ergebnisse: {results_number}, Ziel-Limit: {limit}")
            if check_captcha(driver):
                print("CAPTCHA während der Paginierung erkannt.")
                # search_results könnte hier die bis dahin gesammelten Ergebnisse enthalten
                # oder du entscheidest, -1 zurückzugeben, um den CAPTCHA-Fall klar zu signalisieren
                return -1 # CAPTCHA

            previous_results_count = results_number # Anzahl vor dem Laden der neuen Seite

            try:
                source = driver.page_source
                soup = BeautifulSoup(source, "lxml")

                # Robusterer Selektor für "Nächste Seite". Oft haben diese aria-label oder einen bestimmten Titel.
                # Beispiel: Finde einen Link mit dem Titel "Nächste Seite"
                next_page_link_element = soup.find("a", attrs={"title": next_page, "href": True})
                if not next_page_link_element: # Fallback auf den alten Klassen-Selektor
                    next_page_link_element = soup.find("a", class_=["sb_pagN", "sb_pagN_bp", "b_widePag", "sb_bp"], attrs={"href": True})
                    if next_page_link_element:
                        print("Nächste Seite Link über Klassen gefunden.")
                    else: # Noch ein Versuch: Link mit aria-label "Nächste"
                        next_page_link_element = soup.find("a", attrs={"aria-label": "Page", "href": True})
                        if next_page_link_element:
                           print("Nächste Seite Link über aria-label 'Nächste' gefunden.")


                if next_page_link_element:
                    next_page_href = next_page_link_element["href"]
                    if not next_page_href.startswith("http"):
                        next_page_url = base_url + next_page_href
                    else:
                        next_page_url = next_page_href

                    print(f"Navigiere zu nächster Seite: {next_page_url}")
                    driver.get(next_page_url)
                    time.sleep(random.uniform(2.5, 5.0)) # Längere, variablere Pause
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(0.5, 1.5)) # Kurze Pause nach dem Scrollen

                    page += 1
                    new_page_results = get_search_results(driver, page)

                    if new_page_results:
                        print(f"Seite {page}: {len(new_page_results)} neue potenzielle Ergebnisse gefunden.")
                        search_results.extend(new_page_results)
                        search_results = remove_duplicates(search_results)
                        results_number = len(search_results)
                        print(f"Nach Seite {page}: Insgesamt {results_number} einzigartige Ergebnisse.")

                        if results_number == previous_results_count:
                            # Keine *neuen* einzigartigen Ergebnisse hinzugekommen, obwohl die Seite geladen wurde.
                            # Könnte bedeuten, dass wir am Ende sind oder nur Duplikate auf der Seite waren.
                            print("Keine neuen, einzigartigen Ergebnisse auf dieser Seite. Stoppe Paginierung.")
                            continue_scraping = False
                    else:
                        print(f"Seite {page}: Keine Ergebnisse gefunden. Stoppe Paginierung.")
                        continue_scraping = False
                else:
                    print("Kein 'Nächste Seite'-Link mehr gefunden. Paginierung beendet.")
                    continue_scraping = False

            except Exception as e:
                print(f"Fehler während der Paginierung oder beim Verarbeiten der Seite {page}: {str(e)}")
                continue_scraping = False # Bei Fehlern die Schleife sicherheitshalber verlassen

        # Die Schleife ist beendet (Limit erreicht, keine nächste Seite, Fehler, etc.)
        # Gib die ersten 'limit' (das ursprüngliche, nicht effective_limit) Ergebnisse zurück,
        # falls mehr gesammelt wurden.
        return search_results[:limit] if search_results != -1 else -1

    except Exception as e:
        print(f"Ein schwerwiegender Fehler ist aufgetreten: {str(e)}")
        import traceback
        traceback.print_exc() # Gibt mehr Details zum Fehler aus
        return -1 # Allgemeiner Fehler
    finally:
        if driver:
            try:
                driver.quit()
                print("WebDriver wurde geschlossen.")
            except Exception as e:
                print(f"Fehler beim Schließen des WebDrivers: {e}")