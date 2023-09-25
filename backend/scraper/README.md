# Scraper
The scraper application is a software to collect search results from any information retrieval or search engine. 

## Set up the app

- Change **/backend/config/config_db.ini/config_db.ini** to connect the app to the rat database

## Set up scrapers

- The scraper application is a framework to scrape search results from any information retrieval system. Adding new scrapers is a complex task, so the application offers a template to add desired scrapers.
- The following requirements must be met to add new scrapers to the software:
- Adding the scraper to the table **searchengine**
| name                              | module                                     | resulttype                                                                                        | country                                                                         |
|-----------------------------------|--------------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| search engine name (e. g. Google) | python file with scraper (e. g. google.py) | foreign key to resulttype table to define the resulttype for the scraper (e. g. 1=organic results | foreign key to country table to choose language and country (e. g. 1 = Germany) |

## Run the app

The app is built on the python background process sheduler, as scraping web pages is time and performance consuming.

- To start the app
```
nohup python classifier_start.py >classifier.out &
```

- To stop the app
```
python classifier_stop.py
```

- Alternatively, you can simply configure cronjobs to run classifier.py
