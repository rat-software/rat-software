"""
Scraper

This class represents a scraper object that is responsible for scraping search results.

Methods:
    __init__(): Initializes the Scraper object.
    __del__(): Destructor for the Scraper object.
    scrape(scraper_jobs, db, scraping, job_server): Performs the scraping of search results.

Args:
    scraper_jobs (list): List of scraper jobs to be executed.
    db (object): Database object.
    scraping (object): Scraping object.
    job_server (str): Job server information.

Example:
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    helper = Helper()

    scraping = Scraping()

    db_cnf = currentdir+"/../config/config_db.ini"

    db_cnf = helper.file_to_dict(db_cnf)

    db = DB(db_cnf)

    path_sources_cnf = currentdir+"/../config/config_sources.ini"

    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']

    scraper_jobs = db.get_scraper_jobs()

    scraper = Scraper()

    scraper.scrape(scraper_jobs, db, scraping, job_server)
"""

import json
import importlib

import os
import sys
import inspect

from datetime import datetime

from libs.lib_db import *
from libs.lib_helper import *
from libs.lib_scraping import *

class Scraper:



    def __init__(self):
        self = self

    def __del__(self):
        print('Classifier object destroyed')

    def scrape(self, scraper_jobs, db, scraping, job_server):

        #Update progress of the scraper jobs
        for scraper_job in scraper_jobs:
            scraper_id = scraper_job['scraper_id']
            counter = scraper_job['counter']
            error_code = 0
            progress = 2
            db.update_scraper_job(progress, counter, error_code, job_server, scraper_id)

        #Scrape jobs
        for scraper_job in scraper_jobs:
            position = 0
            counter = scraper_job['counter']
            scraper_id = scraper_job['scraper_id']
            study = scraper_job['study']
            search_engine = scraper_job['searchengine']
            limit = scraper_job['limit']
            query = scraper_job['query']
            query_id = scraper_job['query_id']
            module = scraper_job['module']
            module = module.replace('.py', '')
            mod_folder = "scrapers."+module

            if not db.check_progress(study, query_id):
                pass
            else:
                try:
                    if db.check_scraper_progress(scraper_id):

                        scraper = importlib.import_module(mod_folder)
                        scraping_results = scraper.run(query, limit, scraping, True)

                        if scraping_results != -1:

                            progress = 1

                            for scraping_result in scraping_results:

                                title = scraping_result[0]
                                description = scraping_result[1]
                                url = scraping_result[2]
                                meta = scraping.get_result_meta(url)
                                ip = meta['ip']
                                main = meta['main']
                                created_at = datetime.now()
                                code = scraping_result[3]
                                img = scraping_result[4]
                                page = scraping_result[5]

                                if position < limit:

                                    if not db.check_duplicate_result(url, main, study, scraper_id):
                                        position+=1

                                        serp = db.insert_serp(scraper_id, page, code, img, created_at, query_id)

                                        db.insert_result(title, description, url, position, created_at, main, ip, study, scraper_id, query_id, serp[0])
                                    else:
                                        pass

                            db.update_scraper_job(progress, counter, error_code, job_server, scraper_id)

                            if len(scraping_results) < limit:
                                progress = 3
                                db.update_scraper_job(progress, counter, error_code, job_server, scraper_id)

                        else:
                            progress = -1
                            counter+=1
                            db.update_scraper_job(progress, counter, error_code, job_server, scraper_id)

                except Exception as e:
                    print(str(e))
                    progress = -1
                    counter+=1
                    db.update_scraper_job(progress, counter, error_code, job_server, scraper_id)



if __name__ == "__main__":

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    helper = Helper()

    scraping = Scraping()

    db_cnf = currentdir+"/../config/config_db.ini"
     
    db_cnf = helper.file_to_dict(db_cnf)

    db = DB(db_cnf)
    
    path_sources_cnf = currentdir+"/../config/config_sources.ini"
    
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']

    scraper_jobs = db.get_scraper_jobs()

    print(scraper_jobs)

    scraper = Scraper()

    scraper.scrape(scraper_jobs, db, scraping, job_server)
