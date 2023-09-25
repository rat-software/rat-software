#library with functions for web scraping

#import external libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException #used to interrupt loding of websites and needed as workaround to download files with selenium
from selenium.webdriver.common.action_chains import ActionChains #used to simulate pressing of a key

import time

from subprocess import call

def test_chome_version():

    try:
        url = "http://rat-software.org/"
        #initialize Selenium
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)
        driver.implicitly_wait(30)
        driver.get(url)
        time.sleep(2)
        driver.quit()
        return True
    except Exception as e:
        print(str(e))
        return False

if test_chome_version():
    pass
else:
    print("Your Chrome Browser is not up to date. Please update it first, before using the RAT scrapers. The scraping server is developed for Debian or Ubuntu, so it will try to update Chrome automatically.")
    print("If you use another OS, please check out the process to Update your Chrome.")
    call(["bash", "update_chrome_version_debian.sh"])
