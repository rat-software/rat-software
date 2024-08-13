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
    """    
    try:
        # URLs and constants
        language_url = "https://www.bing.com/?cc=fr&setLang=fr"  # Bing French URL
        search_url_base = "https://www.bing.com/search?q="  # Base URL for Bing search
        captcha_marker = "g-recaptcha"  # Marker for CAPTCHA
        results_number = 0  # Number of results collected
        page = 1  # Current page number
        search_results = []  # List to store search results
        limit += 10  # Increase limit to account for pagination

        def get_search_results(driver, page):
            """
            Extracts search results from the current page.

            Args:
                driver: Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of search results with title, description, URL, and metadata.
            """
            results = []
            source = driver.page_source

            # Encode the page source and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(source, "lxml")

            # Remove irrelevant elements
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
            Checks if CAPTCHA is present on the page.

            Args:
                driver: Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, otherwise False.
            """
            return captcha_marker in driver.page_source

        def remove_duplicates(results):
            """
            Removes duplicate results based on URL.

            Args:
                results (list): List of search results.

            Returns:
                list: List of results with duplicates removed.
            """
            seen_urls = {}
            unique_results = []
            for result in results:
                url = result[2]
                if url not in seen_urls:
                    seen_urls[url] = result
                    unique_results.append(result)
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
            extension_dir=ext_path,
            locale_code="fr",
        )
        driver.maximize_window()
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(30)
        driver.get(language_url)
        time.sleep(random.randint(2, 3))  # Random delay to avoid detection

        # Start scraping if no CAPTCHA is present
        if not check_captcha(driver):
            query = query.lower().replace(" ", "+")
            search_url = f"https://www.bing.com/search?q={query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sk=&first=1&FPIG=2B3943B14F6447E0A9D14FAA50F3D51D"
            driver.get(search_url)
            time.sleep(random.randint(2, 3))  # Random delay to avoid detection

            # Get initial search results
            search_results = get_search_results(driver, page)
            results_number = len(search_results)
            start = results_number
            continue_scraping = True

            # Continue scraping until reaching the limit
            while results_number <= limit and continue_scraping:
                if not check_captcha(driver):
                    try:
                        start = results_number if results_number == start else start + 10
                        search_url = f"https://www.bing.com/search?q={query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sk=&first={start}&FPIG=2B3943B14F6447E0A9D14FAA50F3D51D"
                        driver.get(search_url)
                        time.sleep(random.randint(2, 4))  # Random delay to avoid detection
                        page += 1
                        new_results = get_search_results(driver, page)

                        if new_results:
                            search_results.extend(new_results)
                            search_results = remove_duplicates(search_results)
                            results_number = len(search_results)
                        else:
                            continue_scraping = False
                    except Exception as e:
                        print(f"Error: {e}")
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
        print(f"Error: {e}")
        try:
            driver.quit()
        except:
            pass
        return -1
