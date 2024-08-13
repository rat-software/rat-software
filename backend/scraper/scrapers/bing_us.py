from scrapers.requirements import *

def run(query, limit, scraping, headless):
    """
    Scrape search results from Bing in English.

    Args:
        query (str): The search query.
        limit (int): The maximum number of search results to retrieve.
        scraping: An instance of the Scraping class for encoding and screenshots.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        list: A list of search results where each result includes title, description, URL, and metadata.
              Returns -1 if CAPTCHA is encountered or an error occurs.
    """
    try:
        # Define URL and CSS selectors
        # Define constants
        language_url = "https://www.bing.com/?cc=USA&setLang=en"  # Bing German homepage
        search_url_base = "https://www.bing.com/search?q="  # Base URL for Bing search
        captcha_marker = "g-recaptcha"  # Indicator for CAPTCHA
        limit += 10  # Adjust limit for pagination

        # Initialize variables
        page = 1
        search_results = []

        # Function to extract search results from a page
        def get_search_results(driver, page):
            """
            Extract search results from the current page.

            Args:
                driver: Selenium WebDriver instance.
                page (int): Current page number.

            Returns:
                list: List of search results containing title, description, URL, and metadata.
            """
            results = []
            source = driver.page_source

            # Encode page source and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, "lxml")

            # Remove unwanted elements
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

        # Function to check if CAPTCHA is present
        def check_captcha(driver):
            """
            Check if CAPTCHA is present on the page.

            Args:
                driver: Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is detected, False otherwise.
            """
            return captcha_marker in driver.page_source

        # Function to remove duplicate search results based on URL
        def remove_duplicates(results):
            """
            Remove duplicate search results based on URL.

            Args:
                results (list): List of search results.

            Returns:
                list: List of unique search results.
            """
            seen_urls = {}
            unique_results = []
            for i, result in enumerate(results):
                url = result[2]
                if url not in seen_urls:
                    seen_urls[url] = i
                    unique_results.append(result)
            return unique_results

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
            locale_code="en_us",
        )
        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)

        # Open Bing search page
        driver.get(language_url)
        time.sleep(random.randint(2, 3))  # Random delay to avoid detection

        print(check_captcha(driver))

        if not check_captcha(driver):
            # Construct and navigate to the search URL
            query = query.lower().replace(" ", "+")
            search_url = f"{search_url_base}{query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sc=11-4&sk=&first=1&FPIG=2B3943B14F6447E0A9D14FAA50F3D51D"
            driver.get(search_url)
            time.sleep(random.randint(2, 3))  # Random delay to avoid detection

            results_number = 0

            # Get initial search results
            search_results = get_search_results(driver, page)
            results_number = len(search_results)
            print(results_number)
            start = results_number
            continue_scraping = True

            if results_number and results_number > 0:

            # Scrape additional pages until the limit is reached or no more results
                while (results_number <= limit and start <= limit) and continue_scraping:
                    if not check_captcha(driver):
                        try:
                            # Update search URL for the next page
                            search_url = f"{search_url_base}{query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sc=11-4&sk=&first={start + 10}&FPIG=2B3943B14F6447E0A9D14FAA50F3D51D"
                            print(search_url)
                            driver.get(search_url)
                            time.sleep(random.randint(2, 4))  # Random delay to avoid detection
                            page += 1
                            extract_search_results = get_search_results(driver, page)

                            if extract_search_results:
                                search_results.extend(extract_search_results)
                                search_results = remove_duplicates(search_results)
                                results_number = len(search_results)
                                start += 10
                                print(results_number)
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
