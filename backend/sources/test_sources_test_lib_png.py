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

from libs.lib_sources import *

helper = Helper()

global sources_cnf

import webbrowser

if __name__ == "__main__":
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    path_db_cnf = parentdir+"/config/config_db.ini"
    path_sources_cnf = parentdir+"/config/config_sources.ini"

    helper = Helper()

    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    sources = Sources()
    #url = "https://www.sciencedirect.com/science/article/pii/S0048969723022052"
    #url = "https://spiegel.de"
    #url = "https://www.allianz.de/gesundheit/katzenversicherung/wie-alt-werden-katzen/"
    #url ="https://www.eventim.de/campaign/rammstein/"
    #url = "https://metalinjection.net/news/rammstein-drummer-till-has-distanced-himself-from-us-in-recent-years"
    #url = "https://www.tierschutzbund.de/information/hintergrund/heimtiere/hunde/"
    #url = "https://twitter.com/WWEgames/status/1516461630456045569?lang=en"
    #url = "https://www.handelsblatt.com/politik/deutschland/gesundheitspolitik-bund-und-laender-einigen-sich-bei-krankenhausreform-bayern-dagegen/29248806.html"
    #url = "https://www.stahlschlag.de"
    url = "https://www.caterpillar.com/de/brands/cat.html"
    res = sources.save_code(url)
    png = res["bin"]
    
    png = png.decode('ascii')

    html = '<html><head></head><body><img src="data:image/png;base64, '+png+'" /></body></html>'
    f = open("b64_png.html", "w+")
    f.write(str(html))
    f.close()  
    
    

    webbrowser.open("b64_png.html")