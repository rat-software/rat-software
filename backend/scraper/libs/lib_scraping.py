"""
Scraping class for various scraping-related functions.

Methods:
    __init__: Initialize the Scraping object.
    __del__: Destructor for the Scraping object.
    encode_code: Encode code as base64.
    decode_code: Decode base64-encoded code.
    decode_picture: Decode base64-encoded picture.
    get_result_meta: Get metadata for a given URL.
    take_screenshot: Take a screenshot of the browser window.
    get_real_url: Get the real URL after any redirects.

"""

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

import base64
from urllib.parse import urlparse, parse_qs

class Scraping:

    def __init__(self):
        """
        Initialize the Scraping object.
        """        
        self = self

    def __del__(self):
        """
        Destructor for the Scraping object.
        """        
        print('Helper object destroyed')

    def encode_code(self, code):
        """
        Encode code as base64.

        Args:
            code (str): Code to encode.

        Returns:
            str: Base64-encoded code.
        """        
        code = code.encode('utf-8','ignore')
        code = base64.b64encode(code)
        return code

    def decode_code(self, value):
        """
        Decode base64-encoded code.

        Args:
            value (str): Base64-encoded code.

        Returns:
            str: Decoded code.
        """

        try:
            code_decoded = base64.b64decode(value)
            code_decoded = BeautifulSoup(code_decoded, "html.parser")
            code_decoded = str(code_decoded)
        except Exception as e:
            print(str(e))
            code_decoded = "decoding error"
        return code_decoded



    def decode_picture(self, value):
        """
        Decode base64-encoded picture.

        Args:
            value (str): Base64-encoded picture.

        Returns:
            str: Decoded picture.
        """        
        picture = value.tobytes()
        picture = picture.decode('ascii')
        return picture

    def get_result_meta(self, url):
        """
        Get metadata for a given URL.

        Args:
            url (str): URL to get metadata for.

        Returns:
            dict: Dictionary containing the metadata.
        """        
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



    def take_screenshot(self, driver):
        """
        Take a screenshot of the browser window.

        Args:
            driver: WebDriver instance.

        Returns:
            str: Base64-encoded screenshot image.
        """
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
        driver.save_screenshot(screenshot_file)

        # #open screenshot and save as base64
        screenshot = encode_file_base64(self, screenshot_file)

        os.remove(screenshot_file)

        return screenshot #return base64 code of image

    def get_real_url(self, url, driver):
        """
        Get the real URL after any redirects.

        Args:
            url (str): URL to get the real URL for.
            driver: WebDriver instance.

        Returns:
            str: Real URL after any redirects.
        """        
        try:
            driver.get(url)
            time.sleep(4)
            current_url = driver.current_url #read real url (redirected url)
            return current_url
        except Exception as e:
            print(str(e))
            pass
        
    def decode_bing_url(self, url):
        """
        Extrahiert die Ziel-URL direkt aus dem 'u'-Parameter einer Bing-URL
        durch Base64-Dekodierung. Dies ist die beste Methode, wenn Redirects
        über JavaScript gesteuert werden.

        Args:
            url (str): Die ursprüngliche Bing-Redirect-URL.

        Returns:
            str: Die dekodierte Ziel-URL oder die Original-URL bei einem Fehler.
        """
        try:
            # Zerlegt die URL in ihre Bestandteile
            parsed_url = urlparse(url)
            # Extrahiert die Query-Parameter in ein Dictionary
            query_params = parse_qs(parsed_url.query)
            
            # Holt den Wert des 'u'-Parameters
            encoded_url_list = query_params.get('u')
            
            if not encoded_url_list:
                # Falls der 'u'-Parameter nicht existiert, Original-URL zurückgeben
                return url
                
            encoded_url = encoded_url_list[0]
            
            # Bing stellt oft ein 'a1' voran, das wir entfernen
            if encoded_url.startswith('a1'):
                base64_string = encoded_url[2:]
                
                # Base64-Strings benötigen eine bestimmte Länge (Vielfaches von 4).
                # Wir fügen Füllzeichen hinzu, um Fehler zu vermeiden.
                padding = len(base64_string) % 4
                if padding:
                    base64_string += '=' * (4 - padding)
                
                # Dekodieren des Strings
                decoded_bytes = base64.urlsafe_b64decode(base64_string)
                return decoded_bytes.decode('utf-8')
            else:
                # Falls das Format unerwartet ist, Original-URL zurückgeben
                return url
                
        except Exception as e:
            print(f"Fehler beim Dekodieren der URL {url}: {e}")
            return url # Bei jedem anderen Fehler die Original-URL zurückgeben