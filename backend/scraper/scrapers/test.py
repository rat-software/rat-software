#https://github.com/seleniumbase/SeleniumBase/blob/master/seleniumbase/plugins/driver_manager.py

from scrapers.requirements import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)


ext_path = parentdir+"\i_care_about_cookies_unpacked"

from seleniumbase import Driver
import time

headless = False

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
        #mobile=True,
        )

driver.set_window_size(1920, 1080)
driver.set_page_load_timeout(20)
driver.implicitly_wait(30)
random_sleep = random.randint(2, 5)
time.sleep(random_sleep)
driver.get("https://duckduckgo.com/?t=h_&q=test&ia=web")
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll down to load the whole search engine result page
random_sleep = random.randint(2, 5)
next = driver.find_element(By.XPATH, "//button[@id='more-results']")
next.click()
time.sleep(random_sleep)
driver.quit()