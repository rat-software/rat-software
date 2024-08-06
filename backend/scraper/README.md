# Scraper

The Scraper application is designed to collect search results from various information retrieval systems or search engines.

## Setting Up Scrapers

- The Scraper application provides a framework for scraping search results from different sources. To add new scrapers, follow the provided template, as adding a new scraper can be complex.

- **Requirements for Adding New Scrapers:**
  - Register the new scraper in the `searchengine` table.

  | Name                  | Module                           | Result Type                | Country                 |
  |-----------------------|----------------------------------|----------------------------|-------------------------|
  | Search Engine Name    | Python file with scraper (e.g., `your_scraper.py`) | Foreign key to `resulttype` table (e.g., 1 = organic results) | Foreign key to `country` table (e.g., 1 = Germany) |

- Define your scraper using the template located at **/backend/scrapers/scraper/template_new_scraper.py**. The template provides guidance on how to implement a new scraper.
- Save your new scraper with the desired filename at **/scraper/scrapers/your_scraper.py**.

## Customizing Language and Location

Customizing language and location for scrapers can be challenging. We are working on adapting the browser language in Selenium and using URL parameters to set the location for search engines.

For Google, you can specify the local location using parameters such as `hl` (language), `gl` (global location), and `uule` (URL encoded location). Example URL:
https://www.google.com/search?q=biden&hl=en&gl=US&uule=w+CAIQICImV2VzdCBOZXcgWW9yayxOZXcgSmVyc2V5LFVuaXRlZCBTdGF0ZXM%3D

More information on URL parameters:
- [Google UULE Parameter](https://valentin.app/uule.html)
- [Google URL Parameters Overview](https://padavvan.github.io/)

For Bing, use the parameters `cc` (location) and `setLang` (language). Example URL:
https://www.bing.com/cc=us&setLang=en

More information on Bing parameters:
- [Bing Query Parameters](https://github.com/MicrosoftDocs/bing-docs/blob/main/bing-docs/bing-news-search/reference/query-parameters.md#setlang)


## Configuring the Selenium Driver

Update the language parameter of your Selenium Driver instance. Every scraper should include the following driver configuration:

```python
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
    locale_code="de"  # Language code for the Driver Instance
)
```

## Available Jupyter Notebooks
We also offer a Jupyter Notebook for setting up and testing a new scraper directly, available at [/templates/new_scraper.ipynb](https://github.com/rat-software/rat-software/blob/main/templates/new_scraper.ipynb).

## Running the Application

The application is based on the Python background process Sheduler, as scraping web pages is time and performance consuming.

- To Start the Application:
```
nohup python scraper_controller_start.py
```

- To Stop the Application
```
python scraper_controller_stop.py
```

- Alternative Method:
- Configure cron jobs to run `scraper_start.py` and `scraper_reset.py`.

## Test Scripts for Scrapers
- `scraper_check.py`: Run this script to test if the scrapers are functioning correctly in your application.
- `test_scraper.py` Use this script to test individual scrapers, including any newly added ones.

- To Run a Regular Test of Scrapers:
```
nohup python scraper_controller_start_check.py
```
- To Stop the Test Script:
```
python scraper_controller_stop_check.py
```
