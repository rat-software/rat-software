"""
This script offers a function to verify the functionality of all implemented scrapers. It is recommended to use this script to ensure that the scrapers are still operational.

Scrapers that are not functioning correctly will be marked with a status of -1 in the "test" column of the "searchengine" table.
"""

import os
import sys
import importlib
import inspect

from libs.lib_scraping import *
from libs.lib_db import *
from libs.lib_helper import *
from scrapers.requirements import *

# Determine the current and parent directory paths
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)

# Initialize helper and database configurations
helper = Helper()
db_cnf_path = os.path.join(parentdir, "config", "config_db.ini")

# Load database configuration from file
db_cnf = helper.file_to_dict(db_cnf_path)
db = DB(db_cnf)

def get_scrapers():
    """
    Retrieve the list of scrapers (search engines) from the database.

    Returns:
        list: List of tuples where each tuple represents a search engine.
              The tuple typically contains an ID, name, module name, and status.
    """
    searchengines = db.get_searchengines()
    return searchengines

# Get the list of available search engines
searchengines = get_scrapers()

for se in searchengines:
    print(f"Processing search engine: {se[1]}")

    # Define the query and parameters for scraping
    query = "test"
    se_id = se[0]  # Search engine ID
    se_name = se[1]  # Search engine name
    se_module_name = "scrapers." + se[2]  # Module path for the search engine
    se_module_name = se_module_name.replace(".py", "")  # Remove '.py' extension
    
    # Dynamically import the search engine module
    scraper_module = importlib.import_module(se_module_name)
    scraper = Scraping()  # Instantiate the Scraping class

    # Run the scraper and fetch results
    search_results = scraper_module.run(query, 20, scraper, 1)
    
    # Initialize result counter
    result_count = 0
    
    if search_results and search_results != -1:
        # Process and print each search result
        for sr in search_results:
            result_count += 1
            print(f"Result {result_count}:")
            print(f"  Title: {sr[0]}")
            print(f"  URL: {sr[1]}")
            print(f"  Description: {sr[2]}")
        
        # Update the database with the test status for the search engine
        db.update_searchengine_test(se_id, 1)
    else:
        # Print error message and update the database if scraping fails
        print("Scraping failed")
        db.update_searchengine_test(se_id, -1)
