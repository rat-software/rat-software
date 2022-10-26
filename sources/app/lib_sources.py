#library with functions for web scraping

#import external libraries

#from seleniumwire import webdriver #selenium extension to get underlying data of http requests pip install selenium-wire

from seleniumwire import webdriver #selenium extension to get underlying data of http requests pip install selenium-wire

from selenium.webdriver.firefox.options import Options #iniatilize the options object

from selenium.common.exceptions import TimeoutException #used to interrupt loding of websites and needed as workaround to download files with selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains #used to simulate pressing of a key

import uuid #used to generate random file names

import time #used to do timeout breaks

import os #used for file management

from urllib import request
from urllib.parse import urlsplit
from urllib.parse import urlparse
import urllib.parse
import socket


import requests


from lib_log import *

import webbrowser

import json



def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

sources_cnf = file_to_dict("config_sources.ini")



#iniatilize the library
current_path = os.path.abspath(os.getcwd())

#iniatilize constant variables

#iniatilize the directories for the extension and for the folder for temporary downlods of files
if os.name == "nt":
    extension_path = current_path+"\i_dont_care_about_cookies.xpi"
    download_dir = current_path+'\\tmp'

else:
    extension_path = current_path+"/i_dont_care_about_cookies.xpi"
    download_dir = current_path+'//tmp'

#iniatilize the options for selenium: headless to use firefox in the background; disable-gpu to prevent gpu errors;
options = Options()

if sources_cnf['headless'] == 1:
    options.add_argument("--headless")

options.add_argument("--disable-gpu")

#base64 encoding to convert the code codes of webpages
import base64

#BeautifulSoup is necessary to beautify the code coded after it has been decoded (especially useful to prevent character errors)
from bs4 import BeautifulSoup

#functions to encode and decode the code codes of webpages
def encode_code(code):
    code = code.encode('utf-8','ignore')
    code = base64.b64encode(code)
    return code

def decode_code(code):
    code_decoded = base64.b64decode(code)
    code_decoded = BeautifulSoup(code_decoded, "html.parser")
    code_decoded = str(code_decoded)
    return code_decoded

#function to encode file content to base64
def encode_file_base64(file):
    f = open(file, 'rb')
    code = f.read()
    code = base64.b64encode(code)
    f.close()
    return code

#function to read the redirected urls of a web page (useful, since some search engines don't return the real url of search results)
def get_real_url(url):
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(60)
    try:
        driver.get(url)
        time.sleep(3)
        final_url = driver.current_url #read real url (redirected url)
        driver.quit()
        return final_url
    except Exception as e:
        print(str(e))
        try:
            driver.quit()
        except:
            pass
        finally:
            return False



def get_request_by_requests(url, final_url):
    content_type = ""
    status_code = -1
    print("requests")
    try:
        headers = requests.head(final_url, timeout=3).headers
        response = requests.get(final_url,  verify=False, timeout=10, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64"})
        content_type = headers['Content-Type']
        status_code = response.status_code
    except:
        try:
            headers = requests.head(url, timeout=3).headers
            response = requests.get(url,  verify=False, timeout=10, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64"})
            content_type = headers['Content-Type']
            status_code = response.status_code
        except:
            import mimetypes
            mt = mimetypes.guess_type(final_url)
            if mt:
                content_type = mt[0]

    dict_request = {"content_type": content_type, "status_code": status_code}
    return dict_request


def get_real_url_request(url):
    try:
        response = requests.get(url)
        if response.history:
            print("Request was redirected")
            for resp in response.history:
                print(resp.status_code, resp.url)
            print("Final destination:")
            print(response.status_code, response.url)
            return response.url
        else:
            return False
    except:
        return False



#function to read the status code and content type of a webpage (important to figure if url is an html or pfd document)
def get_request(driver, url, final_url):
    print(url)
    print("seleniumwire")
    status_code = -1
    content_type = ""

    try:

        try:
            for request in driver.requests: #use seleniumwire to read status code and mime content_type
                if request.response:

                    if request.url == final_url or url == request.url:

                        status_code = request.response.status_code

                        if request.response.status_code == 200:
                            content_type = request.response.headers['Content-Type']

                        else:
                            content_type = "error"

            if not content_type:
                content_type = "text/html"
        except Exception as e:
            pass

        finally:
            try:
                if len(driver.requests) > 0:
                    del driver.requests # clear previously captured requests and HAR entries
            except:
                pass
            #return dictionary with content_type and status_code
            dict_request = {"content_type": content_type, "status_code": status_code}
            return dict_request

    except Exception as e:
        print(str(e))
        print("real error")
        raise Exception("seleniumwire failed")






#function to rename a downloaded file since it is not possible to get the file name directly from selenium
def rename_file(download_dir):

    #get list of all files only in the given directory
    list_of_files = filter( lambda x: os.path.isfile(os.path.join(download_dir, x)),
                            os.listdir(download_dir) )

    #sort list of files based on last modification time in ascending order to get the newest file
    list_of_files = sorted( list_of_files,
                            key = lambda x: os.path.getmtime(os.path.join(download_dir, x))
                            )

    newest_file = list_of_files[-1] #load newest file (todo: check for possibilty of duplicate files)

    file_split = os.path.splitext(newest_file)  #split file name and extension to keep the original file extension

    file_extension = file_split[-1] #store file extension

    new_file_name = download_dir+"/"+str(uuid.uuid1())+file_extension #set new file_name based on the results_id

    os.rename(download_dir+"/"+newest_file, new_file_name) #rename file by results_id

    return new_file_name #return file name

#function with selenium to download a file
def download_file(url):
    code = "error"
    #options to download pdf files
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("plugin.disable_full_page_plugin_for_types", "application/pdf")
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(10)

    try:
        driver.get(url) #try to load the url with selenium

    except TimeoutException: #explot the exception to load the download and rename it
        time.sleep(1)
        #rename downloaded file by method and store the content as base64 before removing the file
        file = rename_file(download_dir)
        bin = encode_file_base64(file)
        os.remove(file)

    finally: #return the base64 code of pdf
        driver.quit()
        return bin

#function to read metadata of an url (hostname and ip)
def get_result_meta(url):
    meta = {}
    ip = "-1"
    main = url
    #parse url to get hostname and socket
    try:
        parsed_uri = urlparse(url)
        hostname = '{uri.netloc}'.format(uri=parsed_uri)
        ip = socket.gethostbyname(hostname)
    except:
        ip = "-1"

    try:
        main = '{0.scheme}://{0.netloc}/'.format(urlsplit(url))
    except:
        main = url

    #write to meta dictionary
    meta = {"ip":ip, "main":main}

    return meta

#function to simulate scrolling on a webpage since webpages may just load dynamic content while scrolling
def simulate_scrolling(driver):
    time.sleep(5)
    try:
        height = driver.execute_script('return document.body.parentNode.scrollHeight')
        if height > 1000:
            max_height = height - 1000
        else:
            max_height = height

        current_scroll_position, new_height= 0, 11
        speed = 7

        #sleeper in between scroll positions

        sleeper = 0

        while current_scroll_position <= new_height:
            current_scroll_position += speed

            if current_scroll_position > max_height:
                break

            sleeper += speed
            if sleeper > 1000:
                time.sleep(3)
                sleeper = 0

            driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            new_height =  driver.execute_script("return document.body.scrollHeight")

    except:
        pass

    return driver

#method to save a screensot based on webdriver with filename
def take_screenshot(driver, url):

    current_path = os.path.abspath(os.getcwd())

    #iniatilize constant variables

    #iniatilize the directories for the extension and for the folder for temporary downlods of files
    if os.name == "nt":
        screenshot_folder = current_path+"\\screenshots\\"


    else:
        screenshot_folder = current_path+"//screenshots//"


    screenshot_file = screenshot_folder+str(uuid.uuid1())+".png"

    driver.maximize_window() #maximize browser window for screenshot
    try:
        driver.execute_script("window.scrollTo(0,1)")
    except:
        pass

    #try to get the whole browser window
    try: #first try based on the document.body
        required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
        required_height+= 50
        driver.set_window_size(required_width, required_height)
        driver.save_screenshot(screenshot_file) #take screenshot
    except: #if document.body is null

        try: #try to get the body of the page
            body_screenshot = driver.find_elemnts(By.TAG_NAME, "body")
            body_screenshot.screenshot(screenshot_file)
        except: #if all fails take screenshot of the browser view
            driver.save_screenshot(screenshot_file) #take screenshot

    #open screenshot and save as base64
    screenshot = encode_file_base64(screenshot_file)

    if sources_cnf['debug_screenshots'] == 0:
        os.remove(screenshot_file)

    return screenshot #return base64 code of image

#main function to save the content from an url
def save_code(url):
    #add error_codes in the future
    error_codes = ""
    code = ""
    content_type = ""
    bin = ""
    dict_request = {}
    final_url = ""
    meta = {"ip":"-1", "main": url}

    try:
        driver = webdriver.Firefox(options=options)

        try:

            driver.install_addon(extension_path, temporary=False)
            #iniatilize web driver with timeout 120
            driver.set_page_load_timeout(sources_cnf['timeout'])

            #initialize implicitly_wait to ensure that dom is completely loaded before scraping it
            driver.implicitly_wait(60)
        except Exception as e:
            error_codes+= "Couldn't install Addon: "+str(e)+"; "

        try:
            try:

                driver.get(url)
                time.sleep(sources_cnf['wait_time'])

                try:
                    final_url = driver.current_url #read real url (redirected url)
                    print(final_url)
                except Exception as e:
                    try:
                        final_url = get_real_url_request(url) #backup if driver.current_url fails
                        if not final_url:
                            final_url = url
                    except Exception as e:
                        final_url = url
                        print(str(e))
                        error_codes+= "Couldn't read the redirected URL: "+str(e)+"; "


                try:

                    if final_url:
                        meta = get_result_meta(final_url)
                    else:
                        meta = get_result_meta(url)

                except Exception as e:
                    error_codes+= "Couldn't read the meta data: "+str(e)+"; "


            except TimeoutException:
                try:
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                except Exception as e:
                    code = "error"
                    error_codes+= "Timeout: " + str(e)+";"

        except Exception as e:
            code = "error"
            error_codes+= "Couldn't reach URL: "+str(e)+"; "


        if code != "error":

            try:
                dict_request = get_request(driver, url, final_url)
            except:
                try:
                    dict_request = get_request_by_requests(url, final_url)
                except:
                    dict_request = {"content_type": "error", "status_code": -1}
                    error_codes+= "Requests failed"

            # if dict_request["status_code"] == -1:
            #     error_codes+= "Status error: -1;"

            if "html" in dict_request["content_type"]: #get code code of webpage if mime = html
                try:
                    time.sleep(sources_cnf['wait_time'])
                    if sources_cnf['scrolling'] == 1:
                        try:
                            driver = simulate_scrolling(driver)

                        except Exception as e:
                            code = "error"
                            error_codes+= "Scrolling failed: "+str(e)+"; "

                    bin = take_screenshot(driver, url)

                    code = driver.page_source
                    code = encode_code(code)

                except Exception as e:
                    code = "error"
                    error_codes+= "Screenshot failed: "+str(e)+"; "

            elif "pdf" in dict_request["content_type"]: #check if mime is pdf
                try:
                    bin = download_file(url)
                    code = "pdf"
                except Exception as e:
                    code = "error"
                    error_codes+= "PDF download failed: "+str(e)+"; "

        driver.quit()

    except Exception as e:
        error_codes+= "Scraping failed: "+str(e)+"; "
        try:
            driver.quit()
        except:
            pass

    result_dict = {"code": code, "bin": bin, "request": dict_request, "final_url": final_url, "meta": meta, "error_codes": error_codes}

    return result_dict

#function to test rendering of scraped urls
def render_url(bin, content_type):
    bin = bin.decode('ascii')
    file_name = str(uuid.uuid1())+".html"
    f = open(file_name,'w+')
    if "html" in content_type:
        render = """<html><head></head><body><embed src=data:image/png;base64,{bin} /></body></html>""".format(bin=bin)

    if "pdf" in content_type:
        render = """<html><head></head><body><embed src=data:application/pdf;base64,{bin} style="width:100%;height:100vh;" /></body></html>""".format(bin=bin)

    f.write(render)
    f.close()

    #Change path to open file in webbrowser
    document = 'file:///'+os.getcwd()+'/' + file_name
    webbrowser.open_new_tab(document)
    time.sleep(1)
    os.remove(file_name)

#additional functions

#function to get the content of a robots.txt file of a domain. it is necessary to get the main url first
def save_robot_txt(main):
    url = main+'robots.txt'
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(10)
    try:
        driver.get(url)
        time.sleep(1)
        code = driver.page_source
        try:
            code = encode_code(code)
        except:
            pass

    except:
        code = False

    driver.quit()

    return code

#function to calculate the loading time of an url
def calculate_loading_time(url):
    driver = webdriver.Firefox(options=options)
    driver.install_addon(extension_path, temporary=False)
    driver.set_page_load_timeout(120)
    loading_time = -1

    try:
        driver.get(url)
        time.sleep(1)
        ''' Use Navigation Timing  API to calculate the timings that matter the most '''
        navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
        responseStart = driver.execute_script("return window.performance.timing.responseStart")
        domComplete = driver.execute_script("return window.performance.timing.domComplete")
        loadStart = driver.execute_script("return window.performance.timing.domInteractive")
        EventEnd = driver.execute_script("return window.performance.timing.loadEventEnd")
        ''' Calculate the performance'''
        backendPerformance_calc = responseStart - navigationStart
        frontendPerformance_calc = domComplete - responseStart
        loadingTime = EventEnd - navigationStart
        loading_time = loadingTime / 1000
    except:
        pass

    driver.quit()

    return loading_time
