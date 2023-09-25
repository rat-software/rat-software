#library with functions for web scraping

#import external libraries

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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

import webbrowser

import json

import zipfile

import os
import inspect

#base64 encoding to convert the code codes of webpages
import base64

#BeautifulSoup is necessary to beautify the code coded after it has been decoded (especially useful to prevent character errors)
from bs4 import BeautifulSoup

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)

from libs.lib_helper import *

from libs.lib_content import *

helper = Helper()

global sources_cnf

sources_cnf = helper.file_to_dict(parentdir+'/../config/config_sources.ini')

global proxy_cnf

proxy_cnf = helper.file_to_dict(parentdir+'/../config/config_proxy.ini')

del helper

PROXY_HOST = proxy_cnf["proxy_host"]  # rotating proxy or host
PROXY_PORT = proxy_cnf["proxy_port"] # port
PROXY_USER = proxy_cnf["proxy_user"] # username
PROXY_PASS = proxy_cnf["proxy_pass"] # password

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


current_path = os.path.abspath(os.getcwd())

if os.name == "nt":
    extension_path = parentdir+'\\..\\crx\I-don-t-care-about-cookies.crx'
    download_dir = parentdir+'\\..\tmp'

else:
    extension_path = parentdir+'//..//crx/I-don-t-care-about-cookies.crx'
    download_dir = parentdir+'//..//tmp'

options = Options()
desired_dpi = 1.0
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
options.add_argument('--no-sandbox')
options.add_argument("--start-maximized")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--hide-scrollbars")

if sources_cnf['headless'] == 1:
    options.add_argument('--headless=new')

options.add_extension(extension_path)
#options.add_argument(f"--force-device-scale-factor={desired_dpi}")


class Sources:

    def __init__(self):
        self = self

    def __del__(self):
        print('Sources object destroyed')


    #main function to save the content from an url
    def save_code(self, url):

        def build_proxy_addon(self, use_proxy=False, user_agent=None):
            path = os.path.dirname(os.path.abspath(__file__))
            chrome_options = webdriver.ChromeOptions()
            if use_proxy:
                pluginfile = 'proxy_auth_plugin.zip'

                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                chrome_options.add_extension(pluginfile)
            if user_agent:
                chrome_options.add_argument('--user-agent=%s' % user_agent)
            driver = webdriver.Chrome(
                os.path.join(path, 'chromedriver'),
                chrome_options=chrome_options)
            return driver


        #functions to encode and decode the code codes of webpages
        def encode_code(self, code):
            code = code.encode('utf-8','ignore')
            code = base64.b64encode(code)
            return code

        def decode_code(self, code):
            code_decoded = base64.b64decode(code)
            code_decoded = BeautifulSoup(code_decoded, "html.parser")
            code_decoded = str(code_decoded)
            return code_decoded

        #function to encode file content to base64
        def encode_file_base64(self, file):
            f = open(file, 'rb')
            code = f.read()
            code = base64.b64encode(code)
            f.close()
            return code


        #function to read metadata of an url (hostname and ip)
        def get_result_meta(self, url):
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

        def get_url_header(self, url):
            try:
                meta = get_result_meta(self, url)
                main = meta["main"]
            except:
                pass
            print(url)
            content_type = ""
            status_code = -1
            try:
                response = requests.get(url,  verify=False, timeout=10, headers ={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"})
                status_code = response.status_code
                try:
                    headers = requests.head(url, timeout=3).headers
                    content_type = headers['Content-Type']

                except:
                    if ("!doctype html" in response.text.lower()) or ("/html>" in response.text.lower()):
                        content_type = "html"
                    

            except:
                import mimetypes
                mt = mimetypes.guess_type(url)
                if mt:
                    content_type = mt[0]

            if status_code == 302:
                status_code = 200
                
            if status_code != 200:
                try:
                    driver = webdriver.Chrome(options=options)
                    driver.set_page_load_timeout(sources_cnf['timeout'])
                    driver.implicitly_wait(60)
                    driver.get(url)

                # Access requests via the `requests` attribute
                    for request in driver.requests:

                        if url or main in request.url:
                            status_code = request.response.status_code
                            content_type = request.response.headers['Content-Type']
                            if status_code == 200 or status_code == 302:
                                break
                        
                        

                    if status_code == 302:
                        status_code = 200

                    driver.quit()
                except Exception as e:
                    print(str(e))
                    pass
                
            if "binary" in content_type:
                content_type = "html"
                
            if "json" in content_type:
                content_type = "html"
                
            if "plain" in content_type:
                content_type = "html"

            print(status_code)
            print(content_type)
            

            dict_request = {"content_type": content_type, "status_code": status_code}
            return dict_request

        def get_pdf(self, url):
            pdf_file = str(uuid.uuid1())+".pdf"
            r = requests.get(url, allow_redirects=True)
            open(pdf_file, 'wb').write(r.content)
            bin = encode_file_base64(self, pdf_file)
            os.remove(pdf_file)
            return bin

        def save_content(attr):
            content = Content()
            for key, value in attr.items():
                if key == "ipinfo":
                    try:
                        content_value = content.get_ipinfo(value)
                        return content_value
                    except Exception as e:
                        pass
            del content



        #method to save a screensot based on webdriver with filename
        def take_screenshot(self, driver):

            def simulate_scrolling(driver, required_height):

                height = required_height
                current_height = 0
                block_size = sources_cnf['block-size']
                scroll_time_in_seconds =  sources_cnf['scroll-time']
                blocks = required_height / block_size
                scrolling = []

                while current_height < height and current_height < sources_cnf['max-height']:
                    current_height+=block_size
                    scroll_to = "window.scrollTo(0,{current_height})".format(current_height=str(current_height))
                    driver.execute_script(scroll_to)
                    height = driver.execute_script('return document.body.parentNode.scrollHeight')
                    driver.execute_script("window.scrollTo(0,1)")
                    time.sleep(scroll_time_in_seconds)

                required_height = driver.execute_script('return document.body.parentNode.scrollHeight')

                print(required_height)

                scrolling = [driver, required_height]

                return scrolling

            current_path = os.path.abspath(os.getcwd())

            #iniatilize constant variables

            #iniatilize the directories for the extension and for the folder for temporary downlods of files
            if os.name == "nt":
                screenshot_folder = parentdir+"\\tmp\\"


            else:
                screenshot_folder = parentdir+"//tmp//"

            screenshot_file = screenshot_folder+str(uuid.uuid1())+".png"

            driver.maximize_window() #maximize browser window for screenshot

            required_height = driver.execute_script('return document.body.parentNode.scrollHeight')

            try:
                driver.execute_script("window.scrollTo(0,1)")
            except:
                pass

            try:
                scrolling = simulate_scrolling(driver, required_height)
                driver = scrolling[0]
                required_height = scrolling[1]
            except Exception as e:
                print(str(e))
                pass

            try:
                driver.execute_script("window.scrollTo(0,1)")
            except:
                pass

            #try to get the whole browser window
            try:
                required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
                if required_width < sources_cnf['min-width']:
                    required_width = sources_cnf['min-width']
                if required_height > sources_cnf['max-height']:
                    required_height = sources_cnf['max-height']
                driver.set_window_size(required_width, required_height)
                driver.save_screenshot(screenshot_file) #take screenshot
            except:

                try: #try to get the body of the page
                    body_screenshot = driver.find_elemnts(By.TAG_NAME, "body")
                    body_screenshot.save_screenshot(screenshot_file)

                except: #if all fails take screenshot of the browser view
                    driver.save_screenshot(screenshot_file) #take screenshot


            #open screenshot and save as base64
            screenshot = encode_file_base64(self, screenshot_file)

            if sources_cnf["debug_screenshots"] == 0:
                pass
                os.remove(screenshot_file)

            return screenshot #return base64 code of image


        #add error_codes in the future
        error_codes = ""
        code = ""
        bin = ""
        dict_request = {}
        final_url = url
        meta = {"ip":"-1", "main": url}
        content_dict = {}
       

        try:

            try:
                dict_request = get_url_header(self, url)
            except:
                dict_request = {"content_type": "error", "status_code": -1}
                error_codes+= "Requests failed"

            if dict_request["status_code"] == 200:
                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(sources_cnf['timeout'])
                driver.implicitly_wait(60)

                try:
                    if sources_cnf["proxy"] == 1:
                        driver = build_proxy_addon(self, use_proxy=True)

                    driver.get(url)
                    time.sleep(sources_cnf['wait_time'])
                    
                    code = driver.page_source
                    if len(code) == 0:
                        code = "error"

                    try:
                        final_url = driver.current_url #read real url (redirected url)
                    except:
                        final_url = url

                    if len(final_url) == 0:
                        final_url = url

                    try:
                        meta = get_result_meta(self, final_url)
                        #ip = meta["ip"]
                    except:
                        error_codes+= "Get result meta failed"

                    # try:
                    #     attr = {"ipinfo":ip}
                    #     content_value = save_content(attr)
                    #     content_dict["ipinfo"] = content_value
                    #
                    # except:
                    #     error_codes+= "Get ipinfo failed"


                except TimeoutException:
                    try:
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except Exception as e:
                        code = "error"
                        error_codes+= "Timeout: " + str(e)+";"



                if code != "error":

                    if "html" in dict_request["content_type"]: #get code code of webpage if mime = html
                        try:


                            time.sleep(sources_cnf['wait_time'])

                            bin = take_screenshot(self, driver)

                            code = driver.page_source
                            code = encode_code(self, code)

                            #create loop to retry if code len == 0 max

                        except Exception as e:
                            code = "error"
                            error_codes+= "Screenshot failed: "+str(e)+"; "

                    elif "pdf" in dict_request["content_type"]: #check if mime is pdf
                        try:
                            bin = get_pdf(self, url)
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

        result_dict = {"code": code, "bin": bin, "request": dict_request, "final_url": final_url, "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

        return result_dict
