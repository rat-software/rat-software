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
        limit += 10  # Adjust limit to handle pagination
        page = 1
        search_results = []

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

        # Navigate to Bing Dutch homepage
        driver.get(language_url)
        time.sleep(random.randint(2, 3))  # Random delay to avoid detection

        if not check_captcha(driver):
            # Perform the search
            query = query.lower().replace(" ", "+")
            search_url = f"{search_url_base}{query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sk=&first=1"
            driver.get(search_url)
            time.sleep(random.randint(2, 3))  # Random delay to avoid detection

            # Collect initial search results
            search_results = get_search_results(driver, page)
            results_number = len(search_results)

            while results_number <= limit:
                if not check_captcha(driver):
                    try:
                        start = results_number if results_number != len(search_results) else results_number + 10
                        search_url = f"{search_url_base}{query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sk=&first={start}"
                        driver.get(search_url)
                        time.sleep(random.randint(2, 4))  # Random delay to avoid detection
                        page += 1
                        new_results = get_search_results(driver, page)

                        if new_results:
                            search_results.extend(new_results)
                            search_results = remove_duplicates(search_results)
                            results_number = len(search_results)
                        else:
                            break
                    except Exception as e:
                        print(f"Error: {e}")
                        break
                else:
                    search_results = -1
                    break

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
