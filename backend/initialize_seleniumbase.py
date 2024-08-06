from seleniumbase import Driver

driver = Driver(
    browser="chrome",
    uc=True,                      # Enable undetected Chromedriver
    headless2=True,               # Run the browser in headless mode
    incognito=False,              # Do not use incognito mode
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    do_not_track=True,            # Enable Do Not Track
    undetectable=True,            # Use undetectable Chromedriver      # Path to the browser extension directory
)

driver.quit()
