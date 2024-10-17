from scrapers.requirements import *

def run(query, limit, scraping, headless):
    """
    Scrape Bing search results in Dutch.

    Args:
        query (str): The search query to execute.
        limit (int): The maximum number of search results to retrieve.
        scraping: An instance of the Scraping class for encoding and screenshots.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        list: A list of search results, each containing [title, description, URL, serp_code, serp_bin, page].
              Returns -1 if CAPTCHA is detected or an error occurs.
    """
    try:
        # Define constants and initial variables
        language_url = "https://www.bing.com/?cc=nl&setLang=nl"  # Bing Dutch homepage URL
        search_url_base = "https://www.bing.com/search?q="  # Base URL for Bing search
        captcha_marker = "g-recaptcha"  # Marker to identify CAPTCHA

        page = 1
        search_results = []
        results_number = 0
        search_box = "q"  # Name attribute of the search box input field
 

        def get_search_results(driver, page):
            """
            Extract search results from the current page.

            Args:
                driver: The Selenium WebDriver instance.
                page (int): Current page number.

            Returns:
                list: List of search results with title, description, URL, and metadata.
            """
            results = []
            source = driver.page_source
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)
            soup = BeautifulSoup(source, "lxml")

            # Clean up unnecessary elements
            for tag in soup.find_all("span", class_=["algoSlug_icon"]):
                tag.extract()
            for tag in soup.find_all("li", class_=["b_algoBigWiki"]):
                tag.extract()

            # Extract search results
            for result in soup.find_all("li", class_=["b_algo", "b_algo_group"]):
                try:
                    title = result.find("a").text.strip() if result.find("a") else "N/A"
                except:
                    title = "N/A"
                try:
                    description = (
                        result.find("p", class_=["b_lineclamp2 b_algoSlug", "b_lineclamp4 b_algoSlug", "b_paractl", "b_lineclamp3 b_algoSlug", "b_lineclamp1 b_algoSlug", "b_dList"]).text.strip()
                        if result.find("p") else
                        result.find("ol", class_=["b_dList"]).text.strip() if result.find("ol") else "N/A"
                    )
                except:
                    description = "N/A"

                try:
                    url = result.find("a")["href"] if result.find("a") else "N/A"
                    if "bing." in url:
                        url = scraping.get_real_url(url)
                except:
                    url = "N/A"

                if url != "N/A" and "http" in url:
                    results.append([title, description, url, serp_code, serp_bin, page])

            return results

        def check_captcha(driver):
            """
            Check if CAPTCHA is present on the page.

            Args:
                driver: The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, False otherwise.
            """
            return captcha_marker in driver.page_source

        def remove_duplicates(results):
            """
            Remove duplicate search results based on URL.

            Args:
                results (list): List of search results.

            Returns:
                list: List of unique search results.
            """
            seen_urls = {}
            for index, result in enumerate(results):
                seen_urls[result[2]] = index
            return [results[i] for i in seen_urls.values()]

        # Initialize Selenium WebDriver
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,
            incognito=False,
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="nl"
        )
        driver.maximize_window()
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(30)

        # Navigate to Bing German homepage
        driver.get(language_url)
        time.sleep(random.randint(3, 4))  # Random delay to prevent detection

        search = driver.find_element(By.NAME, search_box)
        search.send_keys(query)
        search.send_keys(Keys.RETURN)
        time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        try:
            cookie_button = driver.find_element(By.CLASS_NAME, "closeicon")
            cookie_button.click()
        except:
            pass

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
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        source = driver.page_source   
                        soup = BeautifulSoup(source, "lxml")
                        pag = soup.find("a", class_=["sb_pagN sb_pagN_bp b_widePag sb_bp"], attrs={"href": True})
                        next_serp = pag["href"]
                        search_url = "https://www.bing.com/"+next_serp
                        print(search_url)
                        driver.get(search_url)
                        time.sleep(random.randint(2, 4))  # Random delay to avoid detection

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
