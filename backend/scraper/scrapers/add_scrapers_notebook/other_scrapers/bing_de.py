from scrapers.requirements import *

def run(query, limit, scraping, headless):
    try:
        #Definition of args for scraping the search engine
        search_url = "https://www.bing.com/?cc=de" #URL of search engine
        search_box = "sb_form_q.sb_form_ta" #Class name of search box
        captcha = "g-recaptcha" #Source code hint for CAPTCHA
        next_page = "//a[@aria-label='{}']" #CSS to find click on next SERP
        results_number = 0 #initialize results_number
        page = 1 #initialize SERP page
        search_results = [] #initialize search_results list
        limit+=10

        #Definition of custom functions

        #Function to scrape search results
        def get_search_results(driver, page):

            get_search_results = []

            source = driver.page_source


            serp_code = scraping.encode_code(source)

            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")

            for s in soup.find_all("span", class_=["algoSlug_icon"]):
                s.extract()

            for s in soup.find_all("li", class_=["b_algoBigWiki"]):
                s.extract()

            for result in soup.find_all("li", class_=["b_algo", "b_algo_group"]):
                url_list = []
                search_result = []
                result_title = ""
                result_description = ""
                result_url = ""
                try:
                    for title in result.find("a"):
                        result_title+=title.text.strip()
                except:
                    result_title = "N/A"

                try:
                    for description in result.find("p", class_=["b_lineclamp2 b_algoSlug", "b_lineclamp4 b_algoSlug", "b_paractl", "b_lineclamp3 b_algoSlug", "b_lineclamp1 b_algoSlug", "b_dList"]):
                        result_description+=description.text.strip()
                except:
                    try:
                        for description in result.find("ol", class_=["b_dList"]):
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
        if headless == 1:
            options.add_argument('--headless=new')
        options.add_experimental_option("detach", True)
        options.add_argument("--start-maximized")
        options.add_argument("--lang=de")
        options.add_extension(chrome_extension)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        driver.maximize_window()
        random_sleep = random.randint(2, 5)
        time.sleep(random_sleep)

        #Start scraping if no CAPTCHA

        if not check_captcha(driver):

            search = driver.find_element(By.CLASS_NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)

            search_results = get_search_results(driver, page)

            results_number = len(search_results)

            continue_scraping = True

            #Click on next SERP pages as long the toal number of results is lower the limit
            while (results_number < limit) and continue_scraping:
                if not check_captcha(driver):
                    random_sleep = random.randint(2, 5)
                    time.sleep(random_sleep)
                    page+=1
                    #page_label = "Seite "+str(page)
                    page_label = "Page "+str(page)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    try:
                        next = driver.find_element(By.XPATH, next_page.format(page_label))
                        next.click()
                        check_search_results = get_search_results(driver, page)
                        check_search_results_len = len(check_search_results)
                        duplicate_counter = 0

                        for check_search_result in check_search_results:
                            if check_search_result in search_results:
                                duplicate_counter+=1

                        if duplicate_counter < check_search_results_len:
                            search_results+= check_search_results
                            results_number = len(search_results)

                        else:
                            continue_scraping = False

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
            return search_results
    
    
    except Exception as e:
        print(str(e))
        try:
            driver.quit()
        except:
            pass
        search_results = -1
        return search_results