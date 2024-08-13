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
        language_url = "https://www.bing.com/?cc=de&setLang=de"  # Bing German homepage
        search_url_base = "https://www.bing.com/search?q="  # Base URL for Bing search
        captcha_marker = "g-recaptcha"  # Indicator for CAPTCHA
        limit += 10  # Adjust limit for pagination

        # Initialize variables
        page = 1
        search_results = []


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
            locale_code="de"
        )
        driver.maximize_window()
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(30)

        # Navigate to Bing German homepage
        driver.get(language_url)
        time.sleep(random.randint(2, 3))  # Random delay to prevent detection

        print(check_captcha(driver))

        if not check_captcha(driver):
            # Perform the search
            query = query.lower().replace(" ", "+")
            search_url = f"https://www.bing.com/search?q={query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sk=&first=1&FPIG=2B3943B14F6447E0A9D14FAA50F3D51D"
            print(search_url)
            driver.get(search_url)
            time.sleep(random.randint(2, 3))

            results_number = 0

            # Collect initial search results
            search_results = get_search_results(driver, page)
            results_number = len(search_results)
            print(results_number)
            continue_scraping = True

            if results_number and results_number > 0:

            # Continue scraping while within the limit
                while results_number <= limit and continue_scraping:
                    if not check_captcha(driver):
                        try:
                            start = results_number if results_number != len(search_results) else results_number + 10
                            search_url = f"https://www.bing.com/search?q={query}&qs=n&sp=-1&ghc=1&lq=0&pq={query}&sk=&first={start}&FPIG=2B3943B14F6447E0A9D14FAA50F3D51D"
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
