import json
import base64
from bs4 import BeautifulSoup

from urllib import request
from urllib.parse import urlsplit
from urllib.parse import urlparse
import urllib.parse
import socket

import os
import inspect

import uuid #used to generate random file names

import time

class Scraping:

    def __init__(self):
        self = self

    def __del__(self):
        print('Helper object destroyed')

    def encode_code(self, code):
        code = code.encode('utf-8','ignore')
        code = base64.b64encode(code)
        return code

    def decode_code(self, value):


        try:
            code_decoded = base64.b64decode(value)
            code_decoded = BeautifulSoup(code_decoded, "html.parser")
            code_decoded = str(code_decoded)
        except Exception as e:
            print(str(e))
            code_decoded = "decoding error"
        return code_decoded



    def decode_picture(self, value):
        picture = value.tobytes()
        picture = picture.decode('ascii')
        return picture

    def get_result_meta(self, url):
        meta = {}
        ip = "-1"
        main = url
        #parse url to get hostname and socket
        try:
            parsed_uri = urlparse(url)
            hostname = '{uri.netloc}'.format(uri=parsed_uri)
            ip = socket.gethostbyname(hostname)
        except Exception as e:
            print(str(e))
            ip = "-1"

        try:
            main = '{0.scheme}://{0.netloc}/'.format(urlsplit(url))
        except Exception as e:
            print(str(e))
            main = url

        #write to meta dictionary
        meta = {"ip":ip, "main":main}

        return meta

    def get_chrome_extension(self):
        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        if os.name == "nt":
            extension_path = parentdir+'\\..\\crx\I-don-t-care-about-cookies.crx'
        else:
            extension_path = parentdir+'//..//crx/I-don-t-care-about-cookies.crx'
        return extension_path


    def take_screenshot(self, driver):

        #function to encode file content to base64
        def encode_file_base64(self, file):
            f = open(file, 'rb')
            code = f.read()
            code = base64.b64encode(code)
            f.close()
            return code

        current_path = os.path.abspath(os.getcwd())

        #iniatilize constant variables

        #iniatilize the directories for the extension and for the folder for temporary downlods of files
        if os.name == "nt":
            screenshot_folder = current_path+"\\tmp\\"


        else:
            screenshot_folder = current_path+"//tmp//"

        screenshot_file = screenshot_folder+str(uuid.uuid1())+".png"

        time.sleep(2)

        driver.maximize_window() #maximize browser window for screenshot
        
        try:
            driver.execute_script("window.scrollTo(0,1)")
        except Exception as e:
            print(str(e))
            pass

        #try to get the whole browser window
        try: 
            required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
            required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
            
            print(required_height)
            
            scroll = "window.scrollTo(0,{})".format(required_height)
            
            driver.execute_script(scroll)

            required_height+= 50
            
            driver.execute_script("window.scrollTo(0,1)")
            
            driver.set_window_size(required_width, required_height)
            
            driver.maximize_window()
            
            driver.save_screenshot(screenshot_file) #take screenshot
            
        except Exception as e:
            print(str(e)) #next try to get the body of the page

            try: 
                body_screenshot = driver.find_element(By.TAG_NAME, "body")
                body_screenshot.screenshot(screenshot_file)
            except Exception as e:
                print(str(e)) #if all fails take screenshot of the browser view
                driver.save_screenshot(screenshot_file) #take screenshot

        #open screenshot and save as base64
        screenshot = encode_file_base64(self, screenshot_file)

        os.remove(screenshot_file)

        return screenshot #return base64 code of image

    def get_real_url(url, driver):
        try:
            driver.get(url)
            time.sleep(4)
            current_url = driver.current_url #read real url (redirected url)
            driver.quit()
            return current_url
        except Exception as e:
            print(str(e))
            pass
