#library with functions for web scraping

#import external libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException #used to interrupt loding of websites and needed as workaround to download files with selenium
from selenium.webdriver.common.action_chains import ActionChains #used to simulate pressing of a key

from selenium.webdriver.support.ui import Select


import uuid #used to generate random file names

import time #used to do timeout breaks

import os #used for file management

#base64 encoding to convert the code codes of webpages
import base64

#BeautifulSoup is necessary to beautify the code coded after it has been decoded (especially useful to prevent character errors)
from bs4 import BeautifulSoup
from lxml import html

import random
import inspect
import re

import os
import inspect
import string

from fake_useragent import UserAgent

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)

ext_path = parentdir+"/i_care_about_cookies_unpacked"

from seleniumbase import Driver



