import os
import sys
import importlib

from libs.lib_scraping import *
from libs.lib_db import *
from libs.lib_helper import *
from scrapers.requirements import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)

helper = Helper()
db_cnf = currentdir+"/../config/config_db.ini"
     
db_cnf = helper.file_to_dict(db_cnf)
db = DB(db_cnf)

def get_scrapers():
    """
    Check the scrapers.

    Returns:
        list: List of search engines.
    """    
    searchengines = db.get_searchengines()
    return searchengines
              
searchengines = get_scrapers()

for se in searchengines:
    print(se)
    query = "test"
    se_id = se[0]
    se_name = se[1]
    se_module = "scrapers."+se[2]
    se_module = se_module.replace(".py", "")    
    scraper_se = importlib.import_module(se_module)
    scraper = Scraping()
    
    status = se[3]
    

      
    search_results = scraper_se.run(query, 20, scraper, 1)
    
    i = 0
    
    if search_results != -1:
        for sr in search_results:
            i+=1
            print(i)
            print(sr[0])
            print(sr[1])
            print(sr[2])
    else:
        print("Scraping failed")
        
    if search_results != -1:
        db.update_searchengine_test(se_id, 1)
    else:
        db.update_searchengine_test(se_id, -1)
 
    

            

