from scrapers.requirements import *

def run(query, limit, scraping, headless):
    try:
        #Definition of args for scraping the search engine
        search_url = "https://www.ecosia.org/" #URL of search engine
        search_box = "q" #Class name of search box
        captcha = "g-recaptcha" #Source code hint for CAPTCHA
        results_number = 0 #initialize results_number
        page = 0 #initialize SERP page
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

            for result in soup.find_all("div", class_=["result__body"]):
                url_list = []

                for url in result.find_all("a"):
                    url = url.attrs['href']
                if "bing.com/aclick?" in url:
                    pass

                else:
                    search_result = []
                    result_title = ""
                    result_description = ""
                    result_url = ""
                    try:
                        for title in result.find("div", class_=["result__title"]):
                            result_title+=title.text.strip()
                    except:
                        result_title = "N/A"

                    try:
                        for description in result.find("div", class_=["result__description"]):
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
        options.add_argument("window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--lang=en")
        options.add_extension(chrome_extension)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        random_sleep = random.randint(2, 5)
        time.sleep(random_sleep)

        #Start scraping if no CAPTCHA
    

        if not check_captcha(driver):

            search = driver.find_element(By.NAME, search_box)
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
                    try:
                        next_page_url = "https://www.ecosia.org/search?method=index&q="+query+"&p="+str(page)
                        print(next_page_url)
                        driver.get(next_page_url)
                        search_results+= get_search_results(driver, page)
                        results_number = len(search_results)
                    except Exception as e:
                        print(str(e))
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