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

- Define a scraper by using the template **/backend/scrapers/scraper/template_new_scraper.py**. The template explains how to add a new scraper.
- Optionally download the zip file for **/templates/new_scraper.ipynb** to test your scraping approaches before you add it to the software.

## Customisation of language and location is a challenge for scrapers. We are currently working on adapting the browser language in Selenium and using URL parameters from search engines. 

With Google, the local location can be specified by combining the language parameter (hl), the global location parameter (gl) and the uule parameter:
https://www.google.com/search?q=biden&hl=en&gl=US&uule=w+CAIQICImV2VzdCBOZXcgWW9yayxOZXcgSmVyc2V5LFVuaXRlZCBTdGF0ZXM%3D

More information at:
- https://valentin.app/uule.html
- https://padavvan.github.io/

Various parameters are also available at Bing (cc=Location, setLang=Language): https://www.bing.com/cc=us&setLang=en

More info about the parameters in Bing:
https://github.com/MicrosoftDocs/bing-docs/blob/main/bing-docs/bing-news-search/reference/query-parameters.md#setlang


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
