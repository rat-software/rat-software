"""
Main application for scraping sources using the results table in the database.
"""

#load custom libs
from libs.lib_logger import *
from libs.lib_db import *
from libs.lib_sources import *

#load required libs
from datetime import datetime
import json
import time
import threading

import os
import inspect
from libs.lib_helper import *

class SourcesScraper:
    """
    A class to scrape and process source URLs from a database.

    Attributes:
        get_sources (list): List of sources to be scraped, including their IDs and URLs.
        job_server (str): Path to the configuration file of the sources scraper.
        db (object): Database object for querying and updating source information.
        logger (object): Logger object for logging operations and errors.
        sources (object): Sources object for handling source-related operations.

    Methods:
        __init__(get_sources: list, job_server: str, db: object, logger: object, sources: object):
            Initializes the SourcesScraper object with the provided parameters.
        __del__():
            Destructor for the SourcesScraper object.
        scrape():
            Scrapes the source code and screenshots of URLs, updating the database with the results.
    """    

    def __init__(self, get_sources: list, job_server: str, db: object, logger: object, sources: object):
        self.get_sources = get_sources
        self.job_server = job_server
        self.db = db
        self.logger = logger
        self.sources = sources

    def __del__(self):
        """Destroy the sources scraper"""
        print('Sources Scraper object destroyed')


    def scrape(self):

        """
        Scrapes URLs and updates the database with source code and screenshots.

        This method performs the following steps:
        1. Initializes a threading event for managing scrape results.
        2. Iterates over the list of sources to be scraped.
        3. Checks if the source has already been processed.
        4. Handles duplicate sources by updating their records if necessary.
        5. Initiates the scraping process using a separate thread.
        6. Waits for the scraping results, processes them, and updates the database.
        7. Logs errors and status updates throughout the process.

        The method utilizes threading to perform concurrent scraping operations and ensures that the results are processed and updated in the database.
        """

        #initialize an event based dictionary for the scraping results
        result_dict_available = threading.Event()

        def scrape_url(sources_url:list):
            """Local function to scrape the url and set the result dictionary when the event is done."""
            global result_dict # Global variable for the results of the scraping.
            result_dict = sources.save_code(sources_url) # Call of the function from lib_sources to scrape the content of the url.
            result_dict_available.set() # Set the dictionary when it is ready

        # Initialize the sources configuration for the application

        logger.write_to_log("Next \t \t Job\t ") # Call the external function to write the current status to the log file

        #loop through all sources to scrape
        for source_to_scrape in get_sources:
            result_id = source_to_scrape[0] # Id of the result from the result table.
            url = source_to_scrape[1] # URL of the result from the result table.
            progress = 2 # Initialize code 2 for source scraping progres (2 = in_progress)
            created_at = datetime.now() # Get current timestamp.
            
            
            #check the progress of the sources to scrape to prevent the scraping process of existing sources
            if db.check_progress(url, result_id):
                pass
            else:

                try:

                    source_id_check = db.get_source_check(url) # Check if source is already scraped by URL

                    if source_id_check:
                        print("duplicate")
                        print(source_id_check)

                        log = str(source_id_check)+"_"+str(result_id)+"\t"+url+"\tupdate result"

                        logger.write_to_log(log)
                        
                        try:
                            counter = db.get_source_counter_result(result_id)
                        except:
                            counter = 1

                        db.update_result_source(result_id, source_id_check, 1, counter, created_at, job_server)

                        # If source is scraped already and not older than 48 hours, duplicate the content

                        if db.get_result_content(source_id_check):

                            rc = db.get_result_content(source_id_check)
                            ip = rc[0]
                            main = rc[1]
                            final_url = rc[2]

                            if len(final_url) == 0:
                                finalt_url = url

                            db.update_result(result_id, ip, main, final_url)

                    else:
                        if db.get_source_check_by_result_id(result_id):
                            
                            if db.get_result_source_source(result_id):
                                source_id = db.get_result_source_source(result_id)
                                counter = db.get_source_counter_result(result_id)
                            else:
                                source_id = db.insert_source(url, progress, created_at, job_server)
                                source_id = source_id[0]
                                counter = 1
                            created_at = datetime.now() # Get current timestamp.
                            print("new")
                            print(source_id)
                            db.update_result_source(result_id, source_id, 2, counter, created_at, job_server)
                        else:
                            source_id = False

                        if source_id: # If no source_id is found, start the scraping job.

                            try:
                                try:
                                    counter = db.get_source_counter_result(result_id)
                                except:
                                    counter = 1
                                
                                

                                thread = threading.Thread(target=scrape_url(url)) # Start the thread for the scraping process
                                thread.start() # Start the thread.

                                result_dict_available.wait() # Wait here for the result to be available before continuing

                                #Store all results from the dictionary to save them to the database

                                code = result_dict['code'] # Source code of the URL
                                bin = result_dict['bin'] # Screenshot of the URL
                                content_type = result_dict['request']['content_type'] # HTML header content_type of the URL
                                status_code = result_dict['request']['status_code'] # Server status_code of the URL
                                final_url = result_dict['final_url'] # Redirected URL
                                ip = result_dict['meta']['ip'] # IP of the URL
                                main = result_dict['meta']['main'] # Main domain of the URL
                                error_code = result_dict['error_codes'] # Error code of the scraping process, if an error occured
                                content_dict = str(result_dict['content_dict'])

                                # Set progess dependent by the success of the scraping job

                                if len(error_code) == 0:
                                    progress = 1
                                else:
                                    progress = -1
                                    status_code = -1

                                if content_type == 'error' or status_code == -1 or code == 'error':
                                    progress = -1

                                if len(final_url) == 0:
                                    final_url = url

                                try:
                                    db.update_source(source_id, code, bin, progress, content_type, error_code, status_code, created_at, content_dict) # Update source in database
                                    created_at = datetime.now() # Get current timestamp.
                                    db.update_result_source(result_id, source_id, progress, counter, created_at, job_server) # Update source in database
                                    db.update_result(result_id, ip, main, final_url) # Update result in database

                                except Exception as e:
                                    logger.write_to_log("Updating source table failed \t \t \t"+str(e))

                                    log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code

                                    logger.write_to_log(log)

                                    print(str(e))
                                    error_code = "Updating source table failed: "+str(e) # Store the error code in database
                                    error = "error"
                                    progress = -1
                                    status_code = -1
                                    log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                    logger.write_to_log(log)
                                    db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict) # Update source in database with error codes
                                    created_at = datetime.now() # Get current timestamp.
                                    db.update_result_source(result_id, source_id, progress, counter, created_at, job_server) # Update source in database


                            # Store information about failure when the function raises an error
                            except Exception as e:
                                try:
                                    counter = db.get_source_counter_result(result_id)
                                except:
                                    pass
                                print(str(e))
                                error_code = "Source Controller scraping failed: "+str(e) # Store the error code in database
                                error = "error"
                                progress = -1
                                status_code = -1
                                log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                logger.write_to_log(log)
                                db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict) # Update source in database with error codes
                                created_at = datetime.now() # Get current timestamp.
                                db.update_result_source(result_id, source_id, progress, counter, created_at, job_server) # Update source in database



                except Exception as e:
                    print(str(e))
                    error_code = "Process failed Source Controller scraping failed: "+str(e) # Store the error code in database
                    error = "error"
                    progress = -1
                    status_code = -1
        
                    print(counter)
                    log = "Skipped Result:"+str(result_id)+"\t"+str(e)+"\t \t \t "
                    logger.write_to_log(log)
                    db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict) # Update source in database with error codes
                    created_at = datetime.now() # Get current timestamp.
                    db.update_result_source(result_id, source_id, progress, counter, created_at, job_server)

if __name__ == "__main__":
    #Load all necessary config files to connect to the database and load the parameters for the sources scraper
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    path_db_cnf = currentdir+"/../config/config_db.ini"
    path_sources_cnf = currentdir+"/../config/config_sources.ini"
    print(path_db_cnf)

    helper = Helper()

    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    db = DB(db_cnf, job_server, refresh_time)
    logger = Logger()
    sources = Sources()
    get_sources = db.get_sources(job_server) # Call the external function from /libs/lib_db.py to read the results without a source.
    print(get_sources)
    sources_scraper = SourcesScraper(get_sources, job_server, db, logger, sources) #Initialize the sources scraper
    sources_scraper.scrape()

    del logger
    del helper
    del db
    del sources_scraper
    del sources
