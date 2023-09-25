from scrapers.requirements import *

def run(query, limit, scraping, headless):
    try:
        #Definition of args for scraping the search engine
        search_url = "https://www.google.lt/" #URL of search engine
        search_box = "q" #Class name of search box
        captcha = "g-recaptcha" #Source code hint for CAPTCHA
        next_page = "//a[@aria-label='{}']" #CSS to find click on next SERP
        results_number = 0 #initialize results_number
        page = 1 #initialize SERP page
        search_results = [] #initialize search_results list

        #Definition of custom functions

        def search_pagination(source):
            soup = BeautifulSoup(source, features="lxml")
            if soup.find("span", class_=["SJajHc NVbCr"]):
                return True
            else:
                return False

        #Function to set the language of Google
        def set_language(driver):

            driver.get("https://www.google.lt/preferences")

            driver.maximize_window()

            driver.find_element(By.ID, "regionanchormore").click()

            time.sleep(2)

            driver.find_element(By.XPATH, "//div[@id='regionoLT']//span[@class='jfk-radiobutton-radio']").click()

            time.sleep(2)

            driver.find_element(By.CLASS_NAME, "goog-inline-block.jfk-button.jfk-button-action").click()

            time.sleep(2)

            driver.find_element(By.LINK_TEXT, "lietuvių").click()

            time.sleep(2)

        #Function to scrape search results
        def get_search_results(driver, page):

            get_search_results = []

            source = driver.page_source

            serp_code = scraping.encode_code(source)

            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")

            for result in soup.find_all("div", class_=["SoaBEf pvFOzb", "SoaBEf"]):
                url_list = []
                search_result = []
                result_title = ""
                result_description = ""
                result_url = ""
                try:
                    for title in result.find("div", class_=["n0jPhd ynAwRc MBeuO nDgy9d"]):
                        result_title+=title.text.strip()
                except:
                    result_title = "N/A"

                try:
                    for description in result.find("div", class_=["GI74Re nDgy9d"]):
                        result_description+=description.text.strip()
                except:
                    result_description = "N/A"

                try:
                    for url in result.find_all("a"):
                        url = url.attrs['href']
                        if "bing." in url:
                            url = scraping.get_real_url(url)
                        url_list.append(url)
                        result_url = url_list[0]
                except:
                    result_url = "N/A"

                get_search_results.append([result_title, result_description, result_url, serp_code, serp_bin, page])

            return get_search_results

        #Function to check if search engine shows CAPTCHA code
        def check_captcha(driver):
            source = driver.page_source
            if captcha in source:
                return True
            else:
                return False

        chrome_extension = scraping.get_chrome_extension() #Get Path for I don't care about cookies extension

        #initialize Selenium
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--start-maximized")
        if headless == 1:
            options.add_argument('--headless=new')
        options.add_experimental_option("detach", True)
        options.add_extension(chrome_extension)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        set_language(driver) #Call function to set the language for the search engine
        driver.maximize_window()
        random_sleep = random.randint(2, 5)
        time.sleep(random_sleep)
        #
   
        #Start scraping if no CAPTCHA
        if not check_captcha(driver):

            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)

            random_sleep = random.randint(2, 5)
            time.sleep(random_sleep)

            driver.find_element(By.XPATH, "//a[contains(@href, '&tbm=nws')]").click()

            time.sleep(2)

            search_results = get_search_results(driver, page)

            results_number = len(search_results)

            continue_scraping = True

            check_pagination = search_pagination(source = driver.page_source)

            if check_pagination:
                #Click on next SERP pages as long the toal number of results is lower the limit
                while (results_number < limit) and continue_scraping:
                    if not check_captcha(driver):
                        random_sleep = random.randint(2, 5)
                        time.sleep(random_sleep)
                        page+=1
                        page_label = "Page "+str(page)
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        try:
                            next = driver.find_element(By.XPATH, next_page.format(page_label))
                            next.click()
                            search_results+= get_search_results(driver, page)
                            results_number = len(search_results)
                        except:
                            continue_scraping = False
                    else:
                        continue_scraping = False
                        search_results = -1

                if headless == 1:
                    driver.quit()

                return search_results

            else:
                SCROLL_PAUSE_TIME = 1

                while (results_number < limit) and continue_scraping:

                    if not check_captcha(driver):
                        try:
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(SCROLL_PAUSE_TIME)
                            driver.execute_script("return document.body.scrollHeight") + 400
                            page+=1
                            search_results+= get_search_results(driver, page)
                            results_number = len(search_results)
                        except:
                            continue_scraping = False
                    else:
                        continue_scraping = False
                        search_results = -1

                if headless == 1:
                    driver.quit()

                return search_results


        else:
            search_results = -1
            if headless == 1:
                driver.quit()

    except Exception as e:
        print(str(e))
        try:
            driver.quit()
        except:
            pass
        search_results = -1
        return search_results