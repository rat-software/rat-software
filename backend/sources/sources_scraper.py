"""
Main application for scraping sources using the results table in the database.

This script is responsible for scraping source URLs from a database, processing them to extract content and screenshots, and then updating the database with the results. It handles the scraping of URLs, manages threading for concurrent operations, and logs the progress and errors.

Dependencies:
    - datetime: For timestamp operations.
    - json: For handling JSON data (if required).
    - time: For timing-related operations.
    - threading: For concurrent execution.
    - os: For path operations.
    - inspect: For inspecting the current file path.
    - Custom libraries: lib_logger, lib_db, lib_sources, lib_helper
"""

# Import custom libraries
from libs.lib_logger import Logger
from libs.lib_db import DB
from libs.lib_sources import Sources
from libs.lib_helper import *

# Import required libraries
from datetime import datetime
import os
import inspect
import threading

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
        """
        Initializes the SourcesScraper object.

        Args:
            get_sources (list): List of sources to be scraped.
            job_server (str): Path to the job server configuration file.
            db (object): Database object for operations.
            logger (object): Logger object for logging.
            sources (object): Sources object for handling source-related operations.
        """
        self.get_sources = get_sources
        self.job_server = job_server
        self.db = db
        self.logger = logger
        self.sources = sources

    def __del__(self):
        """
        Destructor for the SourcesScraper object.

        Prints a message indicating that the SourcesScraper object has been destroyed.
        """
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

        # Initialize a threading event to signal when scraping results are available
        result_dict_available = threading.Event()

        def scrape_url(url: str):
            """
            Local function to scrape a given URL and signal when the results are available.

            Args:
                url (str): The URL to be scraped.
            """
            global result_dict
            result_dict = self.sources.save_code(url)  # Scrape the URL content
            result_dict_available.set()  # Signal that results are available

        # Log the start of the scraping job
        self.logger.write_to_log("Next \t \t Job\t ")

        # Loop through all sources to be scraped
        for source_to_scrape in self.get_sources:
            result_id = source_to_scrape[0]
            url = source_to_scrape[1]
            progress = 2  # Status code 2 indicates in-progress
            created_at = datetime.now()  # Current timestamp

            # Check if the source has already been processed
            if self.db.check_progress(url, result_id):
                continue

            try:
                # Check if the source is already scraped
                source_id_check = self.db.get_source_check(url)

                if source_id_check:
                    # Handle duplicate sources
                    log = f"{source_id_check}_{result_id}\t{url}\tupdate result"
                    self.logger.write_to_log(log)
                    counter = self.db.get_source_counter_result(result_id) or 1
                    self.db.update_result_source(result_id, source_id_check, 1, counter, created_at, self.job_server)

                    if self.db.get_result_content(source_id_check):
                        rc = self.db.get_result_content(source_id_check)
                        ip, main, final_url = rc

                        if not final_url:
                            final_url = url

                        self.db.update_result(result_id, ip, main, final_url)

                else:
                    # Handle new sources
                    if self.db.get_source_check_by_result_id(result_id):
                        if self.db.get_result_source_source(result_id):
                            source_id = self.db.get_result_source_source(result_id)
                            counter = self.db.get_source_counter_result(result_id)
                        else:
                            source_id = self.db.insert_source(url, progress, created_at, self.job_server)[0]
                            counter = 1

                        created_at = datetime.now()  # Update timestamp
                        self.db.update_result_source(result_id, source_id, 2, counter, created_at, self.job_server)

                    else:
                        source_id = False

                    if source_id:
                        try:
                            # Start a new thread for scraping
                            thread = threading.Thread(target=scrape_url, args=(url,))
                            thread.start()

                            # Wait for the scraping results
                            result_dict_available.wait()

                            # Process and store results
                            code = result_dict['code']
                            bin = result_dict['bin']
                            content_type = result_dict['request']['content_type']
                            status_code = result_dict['request']['status_code']
                            final_url = result_dict['final_url'] or url
                            ip = result_dict['meta']['ip']
                            main = result_dict['meta']['main']
                            error_code = result_dict['error_codes']
                            content_dict = str(result_dict['content_dict'])

                            # Determine progress based on scraping success
                            progress = 1 if not error_code else -1
                            if content_type == 'error' or status_code == -1 or code == 'error':
                                progress = -1

                            # Update the database with scraping results
                            self.db.update_source(source_id, code, bin, progress, content_type, error_code, status_code, created_at, content_dict)
                            self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server)
                            self.db.update_result(result_id, ip, main, final_url)

                            log = f"{source_id}_{result_id}\t{url}\t{progress}\t{error_code}"
                            self.logger.write_to_log(log)

                        except Exception as e:
                            # Handle scraping errors
                            counter = self.db.get_source_counter_result(result_id) or 0
                            error_code = f"Source Controller scraping failed: {e}"
                            progress = -1
                            status_code = -1
                            log = f"{source_id}_{result_id}\t{url}\t{progress}\t{error_code}"
                            self.logger.write_to_log(log)
                            self.db.update_source(source_id, "error", "error", progress, "error", error_code, status_code, created_at, content_dict)
                            self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server)

            except Exception as e:
                # Handle any other errors
                error_code = f"Source Controller scraping failed: {e}"
                progress = -1
                status_code = -1
                log = f"Skipped Result: {result_id}\t{e}"
                self.logger.write_to_log(log)
                self.db.update_source(source_id, "error", "error", progress, "error", error_code, status_code, created_at, content_dict)
                self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server)

if __name__ == "__main__":
    """
    Main entry point for the SourcesScraper script.

    Initializes the necessary objects and performs the scraping operation.
    """
    # Determine the directory containing the configuration files
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    path_db_cnf = os.path.join(currentdir, "../config/config_db.ini")
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")

    # Initialize Helper, Database, Logger, and Sources objects
    helper = Helper()
    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    db = DB(db_cnf, job_server, refresh_time)
    logger = Logger()
    sources = Sources()
    get_sources = db.get_sources(job_server)

    # Initialize the SourcesScraper and start the scraping process
    sources_scraper = SourcesScraper(get_sources, job_server, db, logger, sources)
    sources_scraper.scrape()

    # Cleanup
    del logger
    del helper
    del db
    del sources_scraper
    del sources
