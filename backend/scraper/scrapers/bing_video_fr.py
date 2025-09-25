from scrapers.requirements import *

def run(query, limit, scraping, headless):
    """
    Scrapes search results from Bing in German.

    Args:
        query (str): The search term to query.
        limit (int): Maximum number of search results to retrieve.
        scraping: An instance of the Scraping class for encoding and screenshots.
        headless (bool): If True, runs the browser in headless mode.

    Returns:
        list: List of search results where each result is [title, description, url, serp_code, serp_bin, page].
              Returns -1 if CAPTCHA is encountered or an error occurs.
    """
    try:
        # Define constants
        language_url = "https://www.bing.com/?scope=video&nr=1&?cc=fr&setLang=fr"  # Bing German homepage
        captcha_marker = "g-recaptcha"  # Indicator for CAPTCHA
        # Initialize variables
        #limit += 10  # Adjust limit to handle pagination
        page = 1
        search_results = []
        results_number = 0
        search_box = "q"  # Name attribute of the search box input field


        def get_search_results(driver, page):
            """
            Extracts search results from the current page.

            Args:
                driver: The Selenium WebDriver instance.
                page (int): Current page number.

            Returns:
                list: List of search results with title, description, URL, and metadata.
            """
            results = []
            source = driver.page_source

            # Encode page source and capture a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, "lxml")

            # Clean up unnecessary elements
            for tag in soup.find_all("span", class_=["algoSlug_icon"]):
                tag.extract()
            for tag in soup.find_all("li", class_=["b_algoBigWiki"]):
                tag.extract()

            # Extract search results
            for result in soup.find_all("div", class_=["mc_vtvc_meta"]):
                try:
                    # Find div by class and get title attribute
                    div = result.find('div', class_='mc_vtvc_title')
                    if div:
                        title = div.get('title')
                        
                    else:
                        title = "N/A"
                except AttributeError:
                        title = "N/A"

                try:
                    meta_block = result.find('div', class_='mc_vtvc_meta_block_area')
                    if meta_block:
                        # Get all spans and combine their text, skipping any that aren't found
                        texts = []
                        
                        # Try to find each element, skip if not found
                        try:
                            views = meta_block.find('span', class_='meta_vc_content').text
                            texts.append(views)
                        except AttributeError:
                            pass
                            
                        try:
                            date = meta_block.find('span', class_='meta_pd_content').text
                            texts.append(date)
                        except AttributeError:
                            pass
                            
                        try:
                            youtube = meta_block.find_all('span')[2].text
                            texts.append(youtube)
                        except (AttributeError, IndexError):
                            pass
                            
                        try:
                            channel = meta_block.find('span', class_='mc_vtvc_meta_row_channel').text
                            texts.append(channel)
                        except AttributeError:
                            pass
                        
                        # Join all found texts with spaces
                        description = ' '.join(texts)
                        
                    else:
                        description = "N/A"
                except:
                    description = "N/A"                   

                # Find the div with class mc_vtvc_con_rc and get its ourl attribute
                try:
                    div = result.find('div', class_='mc_vtvc_con_rc')
                    if div:
                        ourl = div.get('ourl')
                        url = ourl
                    else:
                        url = "N/A"
                except AttributeError:
                    url = "N/A"                

                if url != "N/A" and "http" in url:
                    results.append([title, description, url, serp_code, serp_bin, page])

                

            return results

        def check_captcha(driver):
            """
            Checks for the presence of CAPTCHA.

            Args:
                driver: The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is present, False otherwise.
            """
            return captcha_marker in driver.page_source

        def remove_duplicates(results):
            """
            Removes duplicate search results based on URL.

            Args:
                results (list): List of search results.

            Returns:
                list: List with duplicates removed.
            """
            seen_urls = {}
            for index, result in enumerate(results):
                seen_urls[result[2]] = index
            return [results[i] for i in seen_urls.values()]

        # Initialize the Selenium WebDriver
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,
            incognito=False,
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="fr"
        )
        driver.maximize_window()
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(30)

        # Navigate to Bing German homepage
        driver.get(language_url)
        time.sleep(random.randint(1, 2))  # Random delay to prevent detection

        search = driver.find_element(By.NAME, search_box)
        search.send_keys(query)
        search.send_keys(Keys.RETURN)
        time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

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

        # Retrieve initial search results and remove duplicates
        
        search_results = get_search_results(driver, page)
        if search_results:
            search_results = remove_duplicates(search_results)
            results_number = len(search_results)
            initial_results_number = len(search_results)
            print(f"Initial search results count for '{query}': {results_number}")       
        
        continue_scraping = True

        #Continue scraping if results are fewer than the limit
        if results_number and results_number > 0:

        # Continue scraping while within the limit
            while results_number <= limit and continue_scraping:
                if not check_captcha(driver):
                    try:                     
                        source = driver.page_source   
                        soup = BeautifulSoup(source, "lxml")
                        pag = soup.find("a", class_=["sb_pagN sb_pagN_bp b_widePag sb_bp"], attrs={"href": True})
                        next_serp = pag["href"]
                        search_url = "https://www.bing.com/"+next_serp
                        print(search_url)
                        driver.quit()
                        # Initialize the Selenium WebDriver
                        driver = Driver(
                            browser="chrome",
                            wire=True,
                            uc=True,
                            headless2=headless,
                            incognito=False,
                            do_not_track=True,
                            undetectable=True,
                            extension_dir=ext_path,
                            locale_code="fr"
                        )
                        driver.maximize_window()
                        driver.set_page_load_timeout(60)
                        driver.implicitly_wait(30)    

                        driver.get(search_url)
                        time.sleep(random.randint(1, 2))  # Random delay to avoid detection

                        page += 1
                        new_results = get_search_results(driver, page)


                        if new_results:
                            search_results.extend(new_results)
                            search_results = remove_duplicates(search_results)
                            results_number = len(search_results)
                            print(results_number)
                            if results_number == initial_results_number:
                                continue_scraping = False
                        else:
                            continue_scraping = False

                    except Exception as e:
                        print(f"Error: {str(e)}")
                        continue_scraping = False
                else:
                    search_results = -1
                    continue_scraping = False

            driver.quit()
            return search_results
        else:
            driver.quit()
            return -1
        
      

    except Exception as e:
        print(f"Error: {str(e)}")
        try:
            driver.quit()
        except:
            pass
        return -1

            
                         

