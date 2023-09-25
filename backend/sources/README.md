# Sources Scraper
The sources scraper is an app that captures the contents of the URLs to be saved both as text and as a screenshot via a background task. The app is designed in such a way that it can be installed on additional servers independently of the main software. The connection to the RAT is made via the common postgresql database.

## Set up the app

- Change config_db.ini to connect the app to the rat database

- Change config_sources.ini to your needs using the following parameters

```
{
    "scrolling": 0, // Some web pages load more dynamic content when scrolling. The source scraper can simulate scrolling behavior, but it is more time consuming. 0 = Scrolling is off; 1 = Scrolling is on
    "wait_time": 5, // Waiting time in seconds before the content of a page is saved. This waiting time is necessary because some web pages need more time to load.
    "debug_screenshots": 0, // 0 = No screenshots are stored locally. 1 = Screenshots are stored locally for debug and analysis purposes.
    "timeout": 60, // Time in seconds before the scraper stops trying to scrape a web page.
    "headless": 1, // Debug variable. 0 = the Firefox browser opens on the local machine. 1 = the Firefox browser does not open on the local machine.
    "job_server": "your server", // You can specify your machine / server here to monitor scraping behavior if you use more than one server for scraping sources.
    "refresh_time": 48 // Some scraping jobs may fail due to technical problems. Change the refresh time in hours as an instruction when to reset the scraping jobs.
}
```

## Run the app

The app is built on the python background process sheduler, as scraping web pages is time and performance consuming.

- To start the app
```
(sources) > nohup python sources_start.py >sources.out &
```

- To stop the app
```
(sources) > python sources_start.py >sources.out &
```

- Alternatively, you can simply configure cronjobs to run sources.py


## Debugging

The app comes with a lib to log the progress in sources.log for debugging.
