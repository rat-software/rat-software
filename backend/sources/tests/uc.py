#test file to implement undetected Chromedriver using selniumbase https://github.com/ultrafunkamsterdam/undetected-chromedriver

import os
import inspect

from pathlib import Path

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)

path = Path(parentdir)

path =str((path.parents[0]))

ext_path = path+"/i_care_about_cookies_unpacked"



from seleniumbase import Driver
import time

driver = Driver(
        browser="chrome",
        uc=True,
        headless2=True,
        incognito=False,
        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        do_not_track=True,
        undetectable=True,
        extension_dir=ext_path,
        )


driver.get('https://spiegel.de')
time.sleep(3)

driver.save_screenshot('uc_test.png') # Wait for 3 seconds to ensure that the browser has fully loaded
driver.quit()