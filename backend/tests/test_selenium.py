#test script to check if Seleniium works correctly

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.common.exceptions import TimeoutException #used to interrupt loding of websites and needed as workaround to download files with selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains #used to simulate pressing of a key

try:
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
    options.add_argument('--no-sandbox')
    options.add_argument("--start-maximized")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--hide-scrollbars")
    options.add_argument('--headless=new')

    test_url = "https://rat-software.org"

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    driver.implicitly_wait(60)
    driver.get(test_url)
    driver.maximize_window() #maximize browser window for screenshot
    driver.save_screenshot("test_screenshot.png") #take screenshot
    driver.quit()
    
    print("Selenium test passed!\nYou can check out the screentshot 'test_screenshot.png' to confirm the success")
    
except Exception as e:
    print("Selenium failed:\n"+str(e))