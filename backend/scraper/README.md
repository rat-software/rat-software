# Scraper
The scraper application is a software to collect search results from any information retrieval or search engine. 

## Set up the app

- Modify **/backend/config/config_db.ini/config_db.ini** to connect the app to the rat database

## Set up scrapers

- The scraper application is a framework to scrape search results from any information retrieval system. Adding new scrapers is a complex task, so the application offers a template to add desired scrapers.
- The following requirements must be met to add new scrapers to the software:
- Adding the scraper to the table **searchengine**
  
| name | module | resulttype | country |
|--------------------|--------------------------|---------------------------------|------------------------------|
| search engine name<br/>(e.g. Google) | python file with scraper<br/>(e. g. google.py) | foreign key to resulttype table<br/>(e. g. 1 = organic results) | foreign key to country table<br/>(e. g. 1 = Germany) |

- Define a scraper by using the template **/scrapers/template_new_scraper.py**. The template explains how to add a new scraper.
- Optionally download the zip file for **/scrapers/add_scrapers_notebook.zip** to test your scraping approaches before you add it to the software.

## Running the application

The application is based on the Python background process Sheduler, as scraping web pages is time and performance consuming.

- To start the application
```
nohup python scraper_controller_start.py
```

- To stop the application
```
python scraper_controller_stop.py
```

- Alternatively, you can simply configure cronjobs that run **scraper_start.py** and **scraper_reset.py**.

## Test script for scraper
- **scraper_check.py**: run the scraper check script to test if the scrapers still work in your application.

- To run a regular test of scrapers
```
nohup python scraper_controller_start_check.py
```
- To stop the application
```
python scraper_controller_stop_check.py
```
