"""
Scraper

This class represents a scraper responsible for executing scraping jobs and updating their progress in the database.

Methods:
    __init__(): Initializes the Scraper object.
    __del__(): Destructor for the Scraper object.
    scrape(scraper_jobs, db, scraping, job_server): Executes the scraping jobs and updates their progress.

Args:
    scraper_jobs (list): List of scraper jobs to be executed.
    db (object): Database object used to interact with the database.
    scraping (object): Scraping object used to perform the actual scraping.
    job_server (str): Information about the job server.

Example:
    # Example usage of Scraper
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    helper = Helper()
    scraping = Scraping()

    db_cnf = os.path.join(currentdir, "../config/config_db.ini")
    db_cnf = helper.file_to_dict(db_cnf)
    db = DB(db_cnf)

    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
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
import time
from datetime import datetime
from libs.lib_db import DB
from libs.lib_helper import Helper
from libs.lib_scraping import Scraping

class Scraper:
    """
    Controller for managing and executing scraping jobs.

    This class handles the execution of scraping tasks and updates their progress in the database.

    Attributes:
        None
    """

    def __init__(self):
        """
        Initializes the Scraper object.
        """
        # No attributes to initialize in this case
        pass

    def __del__(self):
        """
        Destructor for the Scraper object.

        Prints a message indicating the destruction of the Scraper object.
        """
        print('Scraper object destroyed')

    def scrape(self, scraper_jobs, db: DB, scraping: Scraping, job_server: str):
        """
        Executes scraping jobs and updates their progress in the database.

        Args:
            scraper_jobs (list): List of scraper jobs to be executed. Each job is expected to be a dictionary with job details.
            db (DB): Database object used to update job progress and insert results.
            scraping (Scraping): Scraping object used to perform the actual scraping.
            job_server (str): Information about the job server for updating job progress.

        Returns:
            None
        """

        # Update progress for all scraper jobs to indicate they are starting
        for scraper_job in scraper_jobs:
            scraper_id = scraper_job['scraper_id']
            counter = scraper_job['counter']
            error_code = 0
            progress = 2  # Indicates that the job is in progress
            scraper_job_created_at = datetime.now()
            db.update_scraper_job(progress, counter, error_code, job_server, scraper_id, scraper_job_created_at)

        job_counter = len(scraper_jobs)            

        # Process each scraper job
        for scraper_job in scraper_jobs:

            print("Job:"+str(job_counter))

            job_counter = job_counter - 1

            position = 0
            counter = scraper_job['counter']
            scraper_id = scraper_job['scraper_id']

            print("Scraper ID:"+str(scraper_id))

            study = scraper_job['study']
            limit = scraper_job['limit']
            query = scraper_job['query']
            query_id = scraper_job['query_id']
            module = scraper_job['module'].replace('.py', '')
            mod_folder = f"scrapers.{module}"

            # Get result ranges from the database

            range_study = db.get_range_study(study)
            ranges = []

            for r in range_study:
                start = r[0]
                end = r[1]
                for i in range(start, end+1):
                    ranges.append(i)

            if ranges:
                if limit != max(ranges):
                    limit = max(ranges)

            if not db.check_progress(study, query_id):
                continue

            try:
                if db.check_scraper_progress(scraper_id):
                    time.sleep(1)  # Sleep to avoid potential race conditions
                    scraper_module = importlib.import_module(mod_folder)
                    scraping_results = scraper_module.run(query, limit, scraping, True)
                    
                    if scraping_results and scraping_results !=-1:
                        progress = 1  # Indicates successful completion
                        error_code = 0 # Reset error code

                        for scraping_result in scraping_results:
                            position += 1
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
                            meta = scraping.get_result_meta(url)
                            ip = meta['ip']
                            main = meta['main']
                            created_at = datetime.now()
                            
                            if position <= limit:
                                if ranges:
                                    if position in ranges:
                                        if not db.check_duplicate_result(url, main, study, scraper_id, position):
                                            serp = db.insert_serp(scraper_id, page, code, img, created_at, query_id)
                                            db.insert_result(title, description, url, position, created_at, main, ip, study, scraper_id, query_id, serp[0])
                                else:
                                    if not db.check_duplicate_result(url, main, study, scraper_id, position):
                                        serp = db.insert_serp(scraper_id, page, code, img, created_at, query_id)
                                        db.insert_result(title, description, url, position, created_at, main, ip, study, scraper_id, query_id, serp[0])                                   
                            
                        print("Success:"+str(error_code))
                        
                        db.update_scraper_job(progress, counter, error_code, job_server, scraper_id, scraper_job_created_at)

                        # Update job status based on the number of results
                        if len(scraping_results) < limit:
                            error_code = 3 # Indicates partial success
                            if not scraping_results:
                                progress = -1  # Indicates failure
                                print("Error-Code Not enough results:"+str(error_code))
                            db.update_scraper_job(progress, counter, error_code, job_server, scraper_id, scraper_job_created_at)
                    else:
                        # Update job status to failed
                        print("Error-Code Total fail:"+str(error_code))
                        progress = -1 # Indicates failure
                        counter += 1 # Increment job counter
                        error_code = -1 # Set error code
                        db.update_scraper_job(progress, counter, error_code, job_server, scraper_id, scraper_job_created_at)
            except Exception as e:
                # Handle any exceptions during the scraping process
                print(f"Error: {str(e)}")
                progress = -1
                counter += 1
                error_code = -1
                db.update_scraper_job(progress, counter, error_code, job_server, scraper_id, scraper_job_created_at)

if __name__ == "__main__":
    """
    Entry point of the script when executed as the main program.

    - Determines the working directory for configuration files.
    - Loads database and sources configuration.
    - Initializes Scraper and performs the scraping process.
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Load database configuration
    db_cnf = os.path.join(currentdir, "../config/config_db.ini")
    helper = Helper()
    db_cnf = helper.file_to_dict(db_cnf)
    db = DB(db_cnf)

    # Load sources configuration
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
    sources_cnf = helper.file_to_dict(path_sources_cnf)
    job_server = sources_cnf['job_server']

    # Fetch scraper jobs from the database
    scraper_jobs = db.get_scraper_jobs()


    # Fetch failed scraper jobs from the job server
    failed_scraper_jobs = db.get_failed_scraper_jobs_server(job_server)

    scraper_jobs = db.get_all_open_scraper_jobs()
    cleaned_scraper_jobs = []

    scraper = Scraper()


    i = 0
    failed_se = {}

    failed_search_engines = []
   
    for fs in failed_scraper_jobs:
        se = fs['searchengine']
        failed_se[se] = i
        i = i + 1

    
    for key, value in failed_se.items(): 
        if value > 9:
            failed_se = key
            failed_search_engines.append(key)
       
    
    if failed_search_engines:
        cleaned_scraper_jobs = []
        cleaned_scraper_jobs = [sj for sj in scraper_jobs if sj["searchengine"] not in failed_search_engines]
        scraper_jobs = cleaned_scraper_jobs
     

    #Limit the number of scraper jobs to a manageable number
    if len(scraper_jobs) > 2:
        scraper_jobs = scraper_jobs[:2]



    if scraper_jobs:
        scraper.scrape(scraper_jobs, db, Scraping(), job_server)

    # Clean up resources
    del helper
    del db
    del scraper
