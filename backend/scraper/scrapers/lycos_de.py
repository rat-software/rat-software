"""
This template describes the steps necessary to add a custom scraper for the RAT software. First of all, it is assumed that these are search services that provide search forms. However, it is also possible to add other search systems. For this, the procedure would have to be adapted accordingly. Selenium is used as the basis for scraping.

For scraping search results it is necessary to develop the name of the search service to be scraped as well as a scraper Python file for it. In this file appropriate functions must be defined, which are identical for all search engines. However, the contents can also be designed very individually. It is important that at the end search results with the following contents are returned, whereby fields can be filled also empty or with placeholders:

- result_title: title in the snippet of a result
- result_description: description in the snippet of a result
- result_url: url of the search result
- serp_code: html source of the search result page, if it is used for other analyses
- serp_bin: screenshot of the search result page, if it is needed for other analyses
- page: most search engines offer the possibility to browse the result pages. This variable is needed to scroll further. However, for search services where new search results are added by scrolling, it must be adjusted accordingly.

Overall, a scraper usually consists of the following functions:
- run(query, limit, scraping): main function for all scrapers with the following parameters: query = search query, limit = maximum number of results to query, scraping = scraping object with functions to scrape the search engines
- get_search_results(driver, page): subfunction to retrieve the search results with the following parameters:
driver = selenium driver; webbrowser for scraping; page = SERP page
- check_captcha(driver): Helper function to check if there is a lockout of the search services. The function is called to indicate that scraping has been aborted. If checking it is False, the scraping will continue.

The following will describe all standard variables and functionality to scrape a search engine. But again, it is also possible to change it all accordingly to the search engine to be scraped.
"""

from scrapers.requirements import *

def run(query, limit, scraping, headless):
    try:
        #Definition of args for scraping the search engine
        search_url = "https://www.lycos.de/" #URL of search engine, e. g. www.google.de
        search_box = "q" #Class name of search box; input field for searches
        captcha = "g-recaptcha" #Source code hint for CAPTCHA; some search engines use CAPTCHAS to block too many automatic requests
        next_page = "//ul[@class='pagination']" #CSS to find click on next SERP; for search engines that use a navigation on SERPS to continue browsing more search results
        results_number = 0 #initialize results_number; normally starts at 0
        page = 1 #initialize SERP page; normally starts at 1
        search_results = [] #initialize search_results list

        #Definition of custom functions

        #Function to scrape search results
        def get_search_results(driver, page):
            
            counter = 0   #limits amount of search results

            get_search_results = [] #temporary list to store search results

            source = driver.page_source #storing the source code of a search engine result page

            serp_code = scraping.encode_code(source) #use the function from the lib scraping to encode the source code to base64; preparing it to be stored in database

            serp_bin = scraping.take_screenshot(driver) #use the function to take a screenshot, encoding it to base64, to store it in database

            soup = BeautifulSoup(source, features="lxml") #use BeautifulSoup to read the source code of search engine result page and prepare it to read the tree to extract the search results

            #Procedure to read out the search results with title, description and URL. There are several ways to extract such information. In this example we will use functions from BeautifulSoup to read out content of Div containers. Other approaches could be using Selenium or XPATH. Choosing the best way always depends on the search engine.
            
            #first find each block with one result
            
            #sepcial case: find block with no ads and seperate single results
            
            for noAds in soup.find_all("div", class_=["results search-results"]):
                for result in noAds.find_all("li", class_=["result-item"]):
                    url_list = []
                    result_description = "N/A"
                    result_url = "N/A"
                    search_result = []
                    result_title = ""
                    result_description = ""
                
                #try to extract the title based on a css class for the link title
                    try:
                        for title in result.find("h2", class_=["result-title"]):
                            result_title=title.text.strip()
                    except:
                        result_title = "N/A"

                    try:
                    #try to extract the result description by css class and change the content of the description, if necessary:

                        for description in result.find_all("span", class_=["result-description"]):
                            result_description+=description.text.strip()
                            result_description = result_description.replace(result_title, " ")
                            #result_description = result_description.replace("\n", "")
                            result_description = " ".join(result_description.split())
                    except Exception as e:
                        result_description = "N/A"
                    
            #try to extract the urls of the search results and change the url if the search engines works with relative hyperlinks
                    try:
                        for url in result.find_all("a"):
                            url = url.attrs['href']
                            url_list.append(url)
                            result_url = url_list[0]
                    except:
                        result_url = "N/A"
                    
                    if counter < limit+2:                  
                        get_search_results.append([result_title, result_description, result_url, serp_code, serp_bin, page]) #call function to read search results and append the results to the list
                        counter += 1
                    
                return get_search_results


        #Function to check if search engine shows CAPTCHA code. some search engines notice that a bot is trying to scrape their results. if that happens they tend to show a message or captcha
        def check_captcha(driver):
            source = driver.page_source
            if captcha in source:
                return True
            else:
                return False

        #initialize Selenium
        #https://github.com/seleniumbase/SeleniumBase/blob/master/seleniumbase/plugins/driver_manager.py For all options
        #https://seleniumbase.io/help_docs/locale_codes/


        driver = Driver(
                browser="chrome",
                wire=True,
                uc=True,
                headless2=headless,
                incognito=False,
                agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                do_not_track=True,
                undetectable=True,
                extension_dir=ext_path,
                locale_code="de",
                #mobile=True,
                )

        driver.maximize_window()
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(30)
        driver.get(search_url)
        random_sleep = random.randint(2, 5) #random timer trying to prevent quick automatic blocking
        time.sleep(random_sleep)
        

        #Start scraping if no CAPTCHA; not necessary if search engine doesn't use mechanism to block automatic requests
        if not check_captcha(driver):


            #commands to trigger a search; some search engines just use URL GET-pararmeters which could be passed too
            search = driver.find_element(By.NAME, search_box)
            search.send_keys(query)
            search.send_keys(Keys.RETURN)

            random_sleep = random.randint(2, 5) #random timer trying to prevent quick automatic blocking
            time.sleep(random_sleep)                    

            search_results = get_search_results(driver, page)
           
            results_number = len(search_results)

            if results_number > 0:

                continue_scraping = True #check value to stop the scraping loop if CAPTCHAS occur

                #Click on next SERP pages as long the toal number of results is lower the limit; can be replaced in some cases by using the GET-parameters of the search engines url
                while (results_number < limit) and continue_scraping:
                    if not check_captcha(driver):
                        random_sleep = random.randint(2, 5)
                        time.sleep(random_sleep)
                        page+=1 #incremental increase for clicks on the next serp
                        #page_label = "Seite "+str(page) #label to click on serp to continue browing search results
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll down to load the whole search engine result page
                        #try to click on next search engine result page
                        try:
                            next = driver.find_element(By.XPATH, next_page)
                            next.click()
                            search_results+= get_search_results(driver, page)
                            results_number = len(search_results)
                        except Exception as e: #stop scraping if no page label could be found
                            
                            continue_scraping = False
                    else:
                        continue_scraping = False
                        search_results = -1

                driver.quit()
                return search_results


            else:
                search_results = -1
                driver.quit()
                return search_results        
            
        else:
            continue_scraping = False
            search_results = -1
            driver.quit()
            return search_results        

    except Exception as e:
        print(str(e))
        print("Scraping failed")
        try:
            driver.quit()
        except:
            pass
        search_results = -1
        return search_results
    finally:
        try:
            driver.quit()
        except Exception as e:
            print(str(e))
