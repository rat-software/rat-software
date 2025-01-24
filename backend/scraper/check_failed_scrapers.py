import os
import sys
import importlib
import inspect

from libs.lib_scraping import Scraping
from libs.lib_db import DB
from libs.lib_helper import Helper
from scrapers.requirements import *  # Ensure this import is necessary

# Define the current directory and parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)

# Initialize helper and database configuration
helper = Helper()
db_cnf = os.path.join(parentdir, "config", "config_db.ini")

# Load database configuration from file
db_cnf = helper.file_to_dict(db_cnf)
db = DB(db_cnf)

def get_scrapers():
    """
    Retrieve a list of search engines that have failed previously.

    Returns:
        list: A list of tuples representing search engines. Each tuple contains:
            - ID of the search engine
            - Name of the search engine
            - Module name of the search engine
            - Status of the search engine
    """
    searchengines = db.get_failed_searchengines()
    return searchengines

# Get the list of failed search engines
searchengines = get_scrapers()

# Process each search engine
for se in searchengines:
    print(se)
    
    query = "test"  # Sample query for scraping
    se_id = se[0]
    se_name = se[1]
    se_module = f"scrapers.{se[2]}".replace(".py", "")  # Construct module name

    # Dynamically import the search engine module
    scraper_se = importlib.import_module(se_module)
    
    # Initialize scraper instance
    scraper = Scraping()

    # Run the scraper and retrieve search results
    search_results = scraper_se.run(query, 20, scraper, 1)
    
    if search_results and search_results != -1:
        for i, sr in enumerate(search_results, start=1):
            print(i)
            print(sr[0])
            print(sr[1])
            print(sr[2])
        db.update_searchengine_test(se_id, 1)  # Update status to 1 (success)
    else:
        print("Scraping failed")
        db.update_searchengine_test(se_id, -1)  # Update status to -1 (failure)
