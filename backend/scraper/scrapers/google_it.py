from scrapers.requirements import *

def run(query, limit, scraping, headless):
    """
    Scrapes Google IT search results based on the provided query.

    Args:
        query (str): The search query to use for retrieving results.
        limit (int): The maximum number of search results to retrieve.
        scraping: An instance of the Scraping class used for encoding and taking screenshots.
        headless (bool): If True, runs the browser in headless mode (no GUI).

    Returns:
        list: A list of search results where each result contains the title, description, URL, SERP code, screenshot, and page number.
        int: Returns -1 if scraping failed or CAPTCHA is encountered.
    """    
    try:
        # Define constants and initial configurations for scraping
        search_url = "https://www.google.it/webhp?hl=it&gl=IT&uule=w+CAIQICIFSXRhbHk="  # Base URL for Google Italy
        search_box = "q"  # Name attribute of the search box element
        captcha = "g-recaptcha"  # String identifier for CAPTCHA in the HTML source
        next_page = "//a[@aria-label='{}']"  # XPath template for locating the "next" button on search result pages
        next_scroll = "//span[@class='RVQdVd']"  # XPath for locating the "scroll" button for additional results
        results_number = 0  # Counter to keep track of the number of results collected
        page = 1  # Initial page number
        search_results = []  # List to accumulate search results
        get_search_url = "https://www.google.it/search?q="  # Base URL for search result pages
        
        def search_pagination(source):
            """
            Determines if the search results page has pagination.

            Args:
                source (str): The HTML source of the search results page.

            Returns:
                bool: True if pagination is available, False otherwise.
            """
            soup = BeautifulSoup(source, "lxml")
            return bool(soup.find("span", class_=["SJajHc NVbCr"]))

        def get_search_results(driver, page):
            """
            Extracts search results from the current page of search results.

            Args:
                driver (Driver): The Selenium WebDriver instance.
                page (int): The current page number.

            Returns:
                list: A list of search results where each result is a list containing title, description, URL, SERP code, screenshot, and page number.
            """
            results = []

            source = driver.page_source

            # Encode the page source and take a screenshot
            serp_code = scraping.encode_code(source)
            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, "lxml")

            # Remove undesired elements from the search results page
            undesired_classes = ["d4rhi", "Wt5Tfe", "UDZeY fAgajc OTFaAf"]
            for cls in undesired_classes:
                for s in soup.find_all("div", class_=cls):
                    s.decompose()  # Extract elements from the DOM

            # Extract search results from the cleaned page
            for result in soup.find_all("div", class_=["tF2Cxc", "dURPMd"]):
                result_title = ""
                result_description = ""
                result_url = ""

                # Extract title
                try:
                    title = result.find("h3", class_=["LC20lb MBeuO DKV0Md"])
                    if title:
                        result_title = title.text.strip()
                except Exception:
                    result_title = "N/A"

                # Extract description
                try:
                    description = result.find("div", class_=re.compile("VwiC3b", re.I))
                    if description:
                        result_description = description.text.strip()
                except Exception:
                    result_description = "N/A"

                # Extract URL
                try:
                    urls = result.find_all("a")
                    if urls:
                        url = urls[0].attrs.get('href', "N/A")
                        if "bing." in url:
                            url = scraping.get_real_url(url)
                        result_url = url
                except Exception:
                    result_url = "N/A"

                # Append result if the URL is valid
                if result_url != "N/A" and "http" in result_url:
                    results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return results

        def check_captcha(driver):
            """
            Checks if a CAPTCHA is present on the current page.

            Args:
                driver (Driver): The Selenium WebDriver instance.

            Returns:
                bool: True if CAPTCHA is present, False otherwise.
            """
            source = driver.page_source
            return captcha in source

        def remove_duplicates(search_results):
            """
            Removes duplicate search results based on their URL.

            Args:
                search_results (list): The list of search results to deduplicate.

            Returns:
                list: A list of search results with duplicates removed.
            """
            cleaned_results = []
            url_set = set()
            
            for result in search_results:
                url = result[2]
                if url not in url_set:
                    url_set.add(url)
                    cleaned_results.append(result)
            
            return cleaned_results

        # Initialize Selenium WebDriver with specified options
        driver = Driver(
            browser="chrome",
            wire=True,
            uc=True,
            headless2=headless,  # Use headless mode if specified
            incognito=False,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            do_not_track=True,
            undetectable=True,
            extension_dir=ext_path,
            locale_code="it",  # Locale set to Italian
            no_sandbox=True,
        )

        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        time.sleep(random.randint(1, 2))  # Random sleep to avoid detection

        # Start scraping if no CAPTCHA is detected
        if not check_captcha(driver):
            search_box_element = driver.find_element(By.NAME, search_box)
            search_box_element.send_keys(query)
            search_box_element.send_keys(Keys.RETURN)
            time.sleep(random.randint(1, 2))  # Random sleep to avoid detection

            search_results = get_search_results(driver, page)
            search_results = remove_duplicates(search_results)

            results_number = len(search_results)
            print(f"Initial number of search results for '{query}': {results_number}")

            # Continue scraping if the number of results is less than the limit
            if results_number < limit:
                continue_scraping = True
                has_pagination = search_pagination(source=driver.page_source)

                if has_pagination:
                    print("Pagination detected.")
                    # Click on next SERP pages until the result limit is reached
                    while results_number <= limit and page <= (limit / 10) and continue_scraping:
                        if not check_captcha(driver):
                            time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
                            page += 1
                            page_label = f"Page {page}"
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            try:
                                next_page_button = driver.find_element(By.XPATH, next_page.format(page_label))
                                next_page_button.click()
                                search_results += get_search_results(driver, page)
                                search_results = remove_duplicates(search_results)
                                results_number = len(search_results)
                            except Exception as e:
                                print(f"Failed to find or click the next page button: {e}")
                                continue_scraping = False
                        else:
                            continue_scraping = False
                            search_results = -1

                    driver.quit()
                    return search_results

                else:
                    print("No pagination found.")
                    start = 0
                    query = query.lower()
                    get_query = query.replace(" ", "+")
                    search_results = []
                    results_number = 0

                    # Scrape search results by using different start parameters
                    while results_number <= limit and start <= limit and continue_scraping:
                        if not check_captcha(driver):
                            try:
                                edit_search_url = f"{get_search_url}{get_query}&start={start}"
                                print(edit_search_url)
                                driver.get(edit_search_url)
                                time.sleep(random.randint(1, 2))  # Random sleep to avoid detection
                                start += 10
                                extract_search_results = get_search_results(driver, page)

                                if extract_search_results:
                                    print("Appending results.")
                                    search_results += extract_search_results
                                    search_results = remove_duplicates(search_results)
                                    results_number = len(search_results)
                                else:
                                    continue_scraping = False
                                    

                            except Exception as e:
                                print(f"Error: {e}")
                                search_results = -1
                                continue_scraping = False
                        else:
                            continue_scraping = False
                            search_results = -1

                    driver.quit()
                    return search_results
            else:
                driver.quit()
                return search_results

        else:
            search_results = -1
            driver.quit()

    except Exception as e:
        print(f"Error: {e}")
        try:
            driver.quit()
        except Exception as inner_exception:
            print(f"Error during driver quit: {inner_exception}")
        search_results = -1
        return search_results
