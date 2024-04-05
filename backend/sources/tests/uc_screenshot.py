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

def take_screenshot(driver):

        screenshot_file = "test_scrolling.png"

        def simulate_scrolling(driver, required_height):

                height = required_height
                current_height = 0
                block_size = 500
                scroll_time_in_seconds =  2
                scrolling = []

                while current_height < height and current_height < 20000:
                        current_height+=block_size
                        scroll_to = "window.scrollTo(0,{current_height})".format(current_height=str(current_height))
                        driver.execute_script(scroll_to)
                        height = driver.execute_script('return document.body.parentNode.scrollHeight')
                        print(height)
                        driver.execute_script("window.scrollTo(0,1)")
                        time.sleep(scroll_time_in_seconds)

                required_height = driver.execute_script('return document.body.parentNode.scrollHeight')

                scrolling = [driver, required_height]

                return scrolling
        
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


        #try to get the whole browser window
        try:
                required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
                print(required_width)
                if required_width < 1024:
                        required_width = 1024
                if required_height > 20000:
                        required_height = 20000
                driver.set_window_size(required_width, required_height)
                driver.save_screenshot(screenshot_file) #take screenshot
        except:
                driver.save_screenshot(screenshot_file) #take screenshot




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


driver.get('https://stahlschlag.de')
time.sleep(3)

take_screenshot(driver) # Wait for 3 seconds to ensure that the browser has fully loaded
driver.quit()