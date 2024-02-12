"""
This template describes the steps required to add a custom scraper for the RAT software. First of all, it is assumed that these are search services that provide search forms. However, it is also possible to add other search systems. The procedure would have to be adapted accordingly. Selenium is used as the basis for scraping.

A scraper generally consists of the following functions:
- run(query, limit, scraping): Main function for all scrapers with the following parameters: query = search query, limit = maximum number of results to be retrieved, scraping = scraping object with functions for scraping the search engines
- get_search_results(driver, page): Sub-function for retrieving the search results with the following parameters:
driver = Selenium driver; web browser for scraping; page = SERP page
- check_captcha(driver): Helper function to check whether there is a block on search services. The function is called to indicate that scraping has been cancelled. If the check is false, scraping is continued.

All standard variables and functions for scraping a search engine are described below. However, it is also possible to change everything here according to the search engine to be scraped.

Link to the documentation on finding elements on a webpage using Selenium: https://selenium-python.readthedocs.io/locating-elements.html

Adding your scraper to production mode in the software requires additional steps:

1. create a custom Python file for your scraper and add the following line: from scrapers.requirements import *
2. copy the entire main function and paste it into your scraper file
3. add your new scraper to the database in the table 'searchengine', add the name and file name for the scraper and select one of the following result types
of the following result types: 
id	name	                    display	
1	Organic Results	            organic	
2	Snippets	                snippet	
3	Universal Search Results	universal	
4	Advertisements	            ad	
5	News	                    news
"""

#required libs for web scraping

from scrapers.requirements import *

#main function to run a scraper

def run(query, limit, scraping, headless):
    """
    Run the template new scraper.

    Args:
        query (str): The search query.
        limit (int): The maximum number of search results to retrieve.
        scraping: The Scraping object.
        headless (int): Flag indicating whether to run the scraper in headless mode.

    Returns:
        list: List of search results.
    """    
    try:
        #Definition of args for scraping the search engine
        search_url = "https://www.google.de" #URL of search engine, e. g. www.google.de
        search_box = "q" #Class name of search box; input field for searches
        captcha = "g-recaptcha" #Source code hint for CAPTCHA; some search engines use CAPTCHAS to block too many automatic requests
        next_page = "//a[@aria-label='{}']" #CSS to find click on next SERP; for search engines that use a navigation on SERPS to continue browsing more search results
        results_number = 0 #initialize results_number; normally starts at 0
        page = 1 #initialize SERP page; normally starts at 1
        search_results = [] #initialize search_results list

        #Definition of custom functions
        
        def search_pagination(source):
            soup = BeautifulSoup(source, features="lxml")
            if soup.find("span", class_=["SJajHc NVbCr"]):
                return True
            else:
                return False
            
        #Function to scrape search results
        def get_search_results(driver, page):

            get_search_results = []

            source = driver.page_source

            serp_code = scraping.encode_code(source)

            serp_bin = scraping.take_screenshot(driver)

            soup = BeautifulSoup(source, features="lxml")
            
            #addtional steps to extract undesired elements from the Search Engine Result Page (SERP)

            for s in soup.find_all("div", class_="d4rhi"):
                s.extract()

            for s in soup.find_all("div", class_="Wt5Tfe"):
                s.extract()

            for s in soup.find_all("div", class_="UDZeY fAgajc OTFaAf"):
                s.extract()
                
            #find the list with the search results by extracting the div container

            for result in soup.find_all("div", class_=["tF2Cxc"]):
                url_list = []
                search_result = []
                result_title = ""
                result_description = ""
                result_url = ""
                
                #find result title of a search result by header class
                try:
                    for title in result.find("h3", class_=["LC20lb MBeuO DKV0Md"]):
                        result_title+=title.text.strip()
                except:
                    result_title = "N/A"
                    
                
                #find description of a search result by div container
                try:                  
                    for description in result.find("div", class_=re.compile("VwiC3b", re.I)):
                       
                        result_description+=description.text.strip()
                except:
                    result_description = "N/A"
                    
                #find url of a search result by href
                try:
                    for url in result.find_all("a"):
                        url = url.attrs['href']
                        url_list.append(url)
                        result_url = url_list[0]
                except:
                    result_url = "N/A"
                
                #add search results to list
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
        options.add_argument("--lang=de")
        options.add_experimental_option("detach", True)
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

            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)

            random_sleep = random.randint(2, 5)
            time.sleep(random_sleep)

            search_results = get_search_results(driver, page)

            results_number = len(search_results)

            continue_scraping = True

            """
            Custom block to click on the next SERP page:
            
            Google offers two different ways to get more results on a SERP.  Either by clicking on a button for "more results" or by the classic scrolling on the SERP to subsequent pages. This customized block first checks which type of pagination is offered. 
            Subsequent search results are then scraped as long as the total number of search results is less than the defined limit.
            """

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
