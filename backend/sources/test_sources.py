"""
Test script for implementing undetected Chromedriver using SeleniumBase.
For more information, visit: https://github.com/ultrafunkamsterdam/undetected-chromedriver
"""

import os
import inspect
from pathlib import Path
import time
from seleniumbase import Driver

def get_project_path():
    """
    Retrieve the path to the project's root directory.
    
    Returns:
        str: Absolute path to the project's root directory.
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    return str(Path(parentdir))

# Define the path to the browser extension directory
ext_path = os.path.join(get_project_path(), "i_care_about_cookies_unpacked")

# Initialize the SeleniumBase Driver with undetected Chromedriver settings
driver = Driver(
    browser="chrome",
    uc=True,                      # Enable undetected Chromedriver
    headless2=True,               # Run the browser in headless mode
    incognito=False,              # Do not use incognito mode
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    do_not_track=True,            # Enable Do Not Track
    undetectable=True,            # Use undetectable Chromedriver
    extension_dir=ext_path,       # Path to the browser extension directory
)

def main():
    """
    Main function to perform the browser automation task:
    - Open a specific URL
    - Capture a screenshot
    - Close the browser
    """
    url = "https://www.google.com/search?q=versicherungen"
    
    # Open the URL in the browser
    driver.get(url)
    
    # Wait for 3 seconds to ensure that the page has fully loaded
    time.sleep(3)
    
    # Save a screenshot of the current browser view
    driver.save_screenshot('test_sources.png')
    
    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()
