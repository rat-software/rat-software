# Sources Scraper
Sources Scraper is an app that uses a background task to capture the content of URLs to be saved, both as text and as screenshots. The app is designed to be installed on additional servers independently of the main software. The connection to the RAT is established via the common postgresql database.

## Set up the app

- Modify **config_db.ini** to connect the app to the rat database.

- Modify **config_sources.ini** according to your needs with the following parameters.

```
{
    "wait_time": 5,
    "debug_screenshots": 0,
    "timeout": 45,
    "headless": 1,
    "job_server": "your_job_server",
    "refresh_time": 0,
    "proxy": 0,
    "max-height": 20000,
    "min-width": 1024,
    "block-size": 500,
    "scroll-time": 2
}
```
- **wait_time**: Wait time in seconds before the save operation starts.
- **debug_screenshots**: 1 = save a screenshot in the tmp directory; 0 = do not save a screenshot
- **timeout**: Timeout in seconds before the Selenium driver exits if a page could not be loaded.
- **headless**: 1 = use headless mode; 0 = don't use headless mode, show the process in Chrome (best to use on local machines for debugging)
- **job_server**: Name of the machine that will be stored in the database (change it if you use the application on different machines).
- **refresh_time**: Time in hours to prevent the same URLs from being queried at certain times (e.g. 48 if you don't want a source to be queried twice within two days)
- **proxy**: 1 = use a proxy (modify **config_proxy.ini** to add your proxy information); 0 = do not use a proxy.
- **max-height**: maximum height in pixels to subtract from a web page.
- **min-width**: minimum width in pixels
- **block-size**: size of scrolling areas in pixels (e.g. scroll every 500 pixels)
- **scroll-time**: Waiting time in seconds before the application continues scrolling.

## Running the application

The application is based on the Python background process Sheduler, as scraping web pages is time and performance consuming.

- To start the application
```
(sources) > nohup python sources_start.py >sources.out &
```

- To stop the application
```
(sources) > python sources_start.py >sources.out &
```

- Alternatively, you can simply configure cronjobs to run **sources_scraper.py** and **sources_reset.py**.


## Debugging

The application comes with a lib that logs progress to sources.log for debugging.
