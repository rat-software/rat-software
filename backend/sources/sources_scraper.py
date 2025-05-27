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
import concurrent.futures

import os
import inspect
from libs.lib_helper import *

import random
import csv
from libs.lib_proxy_checker import check_proxy, get_working_proxy, get_proxy_for_scraping

import sys

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

    def __init__(self, get_sources: list, job_server: str, db: object, logger: object, sources: object, country: str):
        self.get_sources = get_sources
        self.job_server = job_server
        self.db = db
        self.logger = logger
        self.sources = sources
        self.country = country

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

        def scrape_url(sources_url, proxy, country_code, timeout=450):
            """Thread-sicherer URL-Scraper mit Timeout
            
            Verwendet einen längeren Default-Timeout (450s = 7.5min) und robustere Fehlerbehandlung
            """
            global result_dict  # Deklariere, dass wir die globale Variable nutzen
            
            # Setze result_dict auf None am Anfang
            result_dict = None
            
            try:
                self.logger.write_to_log(f"Starting scrape for URL: {sources_url} with timeout {timeout}s")
                start_time = time.time()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.sources.save_code, sources_url, proxy, country_code)
                    
                    # Versuche, das Ergebnis mit Timeout zu bekommen
                    try:
                        result_dict = future.result(timeout=timeout)
                        elapsed = time.time() - start_time
                        self.logger.write_to_log(f"Scraping completed for {sources_url} in {elapsed:.2f}s")
                    except concurrent.futures.TimeoutError as te:
                        error_msg = f"Scraping timed out after {timeout}s for URL: {sources_url}"
                        self.logger.write_to_log(error_msg)
                        result_dict = {
                            "code": "error",
                            "bin_data": "error",
                            "request": {"content_type": "error", "status_code": -1},
                            "final_url": sources_url,
                            "meta": {"ip": "-1", "main": sources_url},
                            "error_codes": error_msg,
                            "content_dict": {"":""}
                        }
                    except Exception as e:
                        error_msg = f"Error during scraping: {str(e)}"
                        self.logger.write_to_log(error_msg)
                        result_dict = {
                            "code": "error",
                            "bin_data": "error",
                            "request": {"content_type": "error", "status_code": -1},
                            "final_url": sources_url,
                            "meta": {"ip": "-1", "main": sources_url},
                            "error_codes": error_msg,
                            "content_dict": {"":""}
                        }
                
                # Überprüfe, ob result_dict gesetzt wurde
                if result_dict is None:
                    self.logger.write_to_log(f"No result returned for {sources_url} - creating default error result")
                    result_dict = {
                        "code": "error",
                        "bin_data": "error",
                        "request": {"content_type": "error", "status_code": -1},
                        "final_url": sources_url,
                        "meta": {"ip": "-1", "main": sources_url},
                        "error_codes": "No result returned from scraper",
                        "content_dict": {"":""}
                    }
            except Exception as outer_e:
                self.logger.write_to_log(f"Critical error in scrape_url function: {str(outer_e)}")
                result_dict = {
                    "code": "error",
                    "bin_data": "error",
                    "request": {"content_type": "error", "status_code": -1},
                    "final_url": sources_url,
                    "meta": {"ip": "-1", "main": sources_url},
                    "error_codes": f"Critical error: {str(outer_e)}",
                    "content_dict": {"":""}
                }
            finally:
                # Immer Signal setzen, um Deadlocks zu vermeiden
                elapsed = time.time() - start_time
                self.logger.write_to_log(f"Setting result available for {sources_url} after {elapsed:.2f}s")
                result_dict_available.set()

        # Initialize the sources configuration for the application

        #loop through all sources to scrape
        for source_to_scrape in self.get_sources:
            # Definiere die globale Variable result_dict für diese Iteration
            global result_dict
            result_dict = None
            
            result_id = source_to_scrape[0] # Id of the result from the result table.
            url = source_to_scrape[1] # URL of the result from the result table.
            country_proxy = source_to_scrape[2] # Country of the result from the result table.
            country_code = source_to_scrape[3] # Country code of the result from the result table.
   
            # Use our new proxy checker function with Timeout
            try:
                proxy, proxy_error = get_proxy_for_scraping(country_proxy, self.country)
            except Exception as e:
                proxy = None
                proxy_error = f"Proxy selection failed: {str(e)}"
                self.logger.write_to_log(f"Critical proxy error: {proxy_error}")
            
            # Log if there was an error with proxy selection
            if proxy_error:
                log = f"Proxy error for {country_proxy}: {proxy_error}"
                self.logger.write_to_log(log)
                         
            progress = 2 # Initialize code 2 for source scraping progres (2 = in_progress)
            created_at = datetime.now() # Get current timestamp.
            # Initialize content_dict with a default value to avoid undefined reference
            content_dict = {"":""}
            counter = 1  # Initialize counter with a default value
            source_id = None  # Initialize source_id with a default value
            
            #check the progress of the sources to scrape to prevent the scraping process of existing sources
            if self.db.check_progress(url, result_id):
                self.logger.write_to_log(f"Skipping {url} (ID: {result_id}) - already in progress")
                continue
            else:
                try:
                    source_id_check = self.db.get_source_check(url, country_proxy) # Check if source is already scraped by URL

                    if source_id_check:
                        print("duplicate")
                        print(source_id_check)

                        log = str(source_id_check)+"_"+str(result_id)+"\t"+url+"\tupdate result"

                        self.logger.write_to_log(log)
                        
                        try:
                            counter = self.db.get_source_counter_result(result_id)
                        except Exception as e:
                            self.logger.write_to_log(f"Error getting counter for result {result_id}: {str(e)}")
                            counter = 1

                        self.db.update_result_source(result_id, source_id_check, 1, counter, created_at, self.job_server)

                        # If source is scraped already and not older than 48 hours, duplicate the content
                        try:
                            if self.db.get_result_content(source_id_check):
                                rc = self.db.get_result_content(source_id_check)
                                ip = rc[0]
                                main = rc[1]
                                final_url = rc[2]

                                if not(final_url):
                                    final_url = url

                                elif len(final_url) == 0:
                                    final_url = url

                                self.db.update_result(result_id, ip, main, final_url)
                        except Exception as e:
                            self.logger.write_to_log(f"Error updating duplicate content for {result_id}: {str(e)}")

                    else:
                        if self.db.get_source_check_by_result_id(result_id):
                            
                            if self.db.get_result_source_source(result_id):
                                source_id = self.db.get_result_source_source(result_id)
                                counter = self.db.get_source_counter_result(result_id)
                            else:
                                source_id = self.db.insert_source(url, progress, created_at, self.job_server, country_proxy)
                                source_id = source_id[0]
                                counter = 1
                            created_at = datetime.now() # Get current timestamp.
                            print("new")
                            print(source_id)
                            self.db.update_result_source(result_id, source_id, 2, counter, created_at, self.job_server)
                        else:
                            source_id = False

                        if source_id: # If source_id is found, start the scraping job.
                            try:
                                try:
                                    counter = self.db.get_source_counter_result(result_id)
                                except Exception as e:
                                    self.logger.write_to_log(f"Error getting counter for result {result_id}: {str(e)}")
                                    counter = 1
                                
                                # If proxy is needed but no working proxies were found
                                if country_proxy != self.country and country_proxy is not None and proxy is None:
                                    error_code = f"No working proxies available for {country_proxy}: {proxy_error}"
                                    progress = -1
                                    status_code = -1
                                    error = "error"
                                    log = f"{source_id}_{result_id}\t{url}\t{progress}\t{error_code}"
                                    self.logger.write_to_log(log)
                                    self.db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict)
                                    created_at = datetime.now()
                                    self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server)
                                    continue

                                # Setze ein Timeout für den gesamten Scrape-Prozess
                                max_scrape_time = 450  # 7.5 Minuten maximale Laufzeit pro URL
                                start_time = time.time()
                                
                                # Erstelle und starte den Thread mit Argumenten
                                thread = threading.Thread(target=scrape_url, args=(url, proxy, country_code, max_scrape_time))
                                thread.daemon = True  # Daemon-Thread, damit er nicht die Ausführung blockiert
                                thread.start()

                                # Warte auf das Ergebnis mit einem längeren Timeout
                                wait_timeout = max_scrape_time * 1.5  # 50% mehr Zeit als die maximale Scraping-Zeit
                                
                                # Warten mit periodischen Checks
                                wait_start_time = time.time()
                                while not result_dict_available.is_set():
                                    # Kurz warten (5 Sekunden)
                                    result_dict_available.wait(5)
                                    
                                    # Überprüfen, ob wir das Timeout erreicht haben
                                    elapsed = time.time() - wait_start_time
                                    if elapsed > wait_timeout:
                                        self.logger.write_to_log(f"Timeout waiting for result from {url} after {elapsed:.2f}s")
                                        break
                                        
                                    # Periodischer Status-Log
                                    if int(elapsed) % 60 == 0:  # Jede Minute
                                        self.logger.write_to_log(f"Still waiting for result from {url} ({elapsed:.2f}s elapsed)")
                                    
                                    # Prüfen, ob result_dict bereits verfügbar ist
                                    if result_dict is not None:
                                        self.logger.write_to_log(f"Result available for {url} after {elapsed:.2f}s")
                                        break
                                
                                # Überprüfe ob result_dict definiert ist
                                if result_dict is None:
                                    self.logger.write_to_log(f"Result dict not available for {url} after {time.time() - wait_start_time:.2f}s")
                                    result_dict = {
                                        "code": "error",
                                        "bin_data": "error",
                                        "request": {"content_type": "error", "status_code": -1},
                                        "final_url": url,
                                        "meta": {"ip": "-1", "main": url},
                                        "error_codes": "Result unavailable after waiting",
                                        "content_dict": {"":""}
                                    }
                                    
                                # Event zurücksetzen für die nächste Verwendung
                                result_dict_available.clear()

                                #Store all results from the dictionary to save them to the database
                                code = result_dict.get('code', "error") # Source code of the URL
                                bin_data = result_dict.get('bin_data', "error") # Screenshot of the URL
                                content_type = result_dict.get('request', {}).get('content_type', "error") # HTML header content_type of the URL
                                status_code = result_dict.get('request', {}).get('status_code', -1) # Server status_code of the URL
                                final_url = result_dict.get('final_url', url) # Redirected URL
                                ip = result_dict.get('meta', {}).get('ip', "-1") # IP of the URL
                                main = result_dict.get('meta', {}).get('main', url) # Main domain of the URL
                                error_code = result_dict.get('error_codes', "") # Error code of the scraping process, if an error occured

                                # Append proxy information to error_code if there was a proxy error
                                if proxy_error:
                                    if error_code:
                                        error_code += "; " + proxy_error
                                    else:
                                        error_code = proxy_error
                                        
                                try:
                                    content_dict = str(result_dict.get('content_dict', {"":""}))
                                except:
                                    content_dict = {"":""}
                                    
                                timeout_indicators = ["timeout", "timed out", "partial content"]
                                has_timeout = any(indicator in error_code.lower() for indicator in timeout_indicators)

                                # Set progress to -1 if any condition is not met
                                if (status_code != 200 or 
                                    content_type == 'error' or 
                                    code == 'error' or 
                                    bin_data == 'error' or 
                                    has_timeout):
                                    progress = -1
                                else:
                                    progress = 1

                                # Log the progress determination for debugging
                                log_msg = f"Progress set to {progress} for {url}: status={status_code}, content_type={content_type}"
                                if progress == -1:
                                    # Log why progress is set to -1
                                    reasons = []
                                    if status_code != 200:
                                        reasons.append(f"status_code is {status_code} (not 200)")
                                    if content_type == 'error':
                                        reasons.append("content_type is error")
                                    if code == 'error':
                                        reasons.append("source code is error")
                                    if bin_data == 'error':
                                        reasons.append("screenshot is error")
                                    if has_timeout:
                                        reasons.append(f"timeout detected: '{error_code}'")
                                    
                                    log_msg += ", reasons: " + ", ".join(reasons)
                                self.logger.write_to_log(log_msg)

                                if len(final_url) == 0:
                                    final_url = url

                                try:
                                    self.db.update_source(source_id, code, bin_data, progress, content_type, error_code, status_code, created_at, content_dict) # Update source in database
                                    created_at = datetime.now() # Get current timestamp.
                                    self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) # Update source in database
                                    self.db.update_result(result_id, ip, main, final_url) # Update result in database

                                except Exception as e:
                                    self.logger.write_to_log("Updating source table failed \t \t \t"+str(e))

                                    log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code

                                    self.logger.write_to_log(log)

                                    print(str(e))
                                    # Add proxy error information if there was any
                                    proxy_info = f" (Proxy: {proxy})" if proxy else ""
                                    if proxy_error:
                                        proxy_info += f" Proxy issues: {proxy_error}"
                                    
                                    error_code = f"Source Controller scraping failed: {str(e)}{proxy_info}" # Store the error code in database
                                    error = "error"
                                    progress = -1
                                    status_code = -1
                                    content_dict = "error"
                                    log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                    self.logger.write_to_log(log)
                                    self.db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict) # Update source in database with error codes
                                    created_at = datetime.now() # Get current timestamp.
                                    self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) # Update source in database


                            # Store information about failure when the function raises an error
                            except Exception as e:
                                try:
                                    counter = self.db.get_source_counter_result(result_id)
                                except:
                                    counter = 1
                                
                                # Add proxy error information if there was any
                                proxy_info = f" (Proxy: {proxy})" if proxy else ""
                                if proxy_error:
                                    proxy_info += f" Proxy issues: {proxy_error}"
                                    
                                error_code = f"Final Source Controller scraping failed: {str(e)}{proxy_info}" # Store the error code in database
                                print(error_code)
                                error = "error"
                                progress = -1
                                status_code = -1
                                log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                self.logger.write_to_log(log)
                                self.db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict) # Update source in database with error codes
                                created_at = datetime.now() # Get current timestamp.
                                self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) # Update source in database

                except Exception as e:
                    # Add proxy error information if there was any
                    proxy_info = f" (Proxy: {proxy})" if proxy else ""
                    if proxy_error:
                        proxy_info += f" Proxy issues: {proxy_error}"
                        
                    error_code = f"Process failed Source Controller scraping failed: {str(e)}{proxy_info}" # Store the error code in database
                    print(error_code)
                    error = "error"
                    progress = -1
                    status_code = -1
                    # content_dict is now initialized at the beginning of the loop
                    content_dict = "error"  # Setting it again here for clarity
                    log = "Skipped Result:"+str(result_id)+"\t"+str(e)+"\t \t \t "
                    self.logger.write_to_log(log)
                    if source_id:  # Only update if source_id exists
                        self.db.update_source(source_id, error, error, progress, error, error_code, status_code, created_at, content_dict) # Update source in database with error codes
                        created_at = datetime.now() # Get current timestamp.
                        self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) # Update source in database

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
    country = sources_cnf['country']

    # Fehlerbehandlung für Datenbankkonfiguration
    try:
        db = DB(db_cnf, job_server, refresh_time)
        if not db.check_db_connection():
            print("Datenbankverbindung konnte nicht hergestellt werden. Beende...")
            sys.exit(1)
    except Exception as e:
        print(f"Fehler bei der Initialisierung der Datenbankverbindung: {str(e)}")
        sys.exit(1)

    logger = Logger()
    sources = Sources()

    # Fehlerbehandlung für get_sources
    try:
        get_sources = db.get_sources(job_server) # Call the external function from /libs/lib_db.py to read the results without a source.
        if not get_sources:
            print("Keine Quellen zum Scrapen gefunden.")
            logger.write_to_log("No sources to scrape found")
            # Clean up
            del logger
            del helper
            del db
            del sources
            sys.exit(0)
    except Exception as e:
        print(f"Fehler beim Abrufen der Quellen: {str(e)}")
        logger.write_to_log(f"Error getting sources: {str(e)}")
        # Cleanup
        del logger
        del helper
        del db
        del sources
        sys.exit(1)

    print(get_sources)

    # Setze Gesamttimeout für den Scraper
    MAX_TOTAL_RUNTIME = 7200  # 2 Stunden maximale Laufzeit für den gesamten Scraper
    start_time = time.time()

    sources_scraper = SourcesScraper(get_sources, job_server, db, logger, sources, country) #Initialize the sources scraper
    
    try:
        # Verwende ThreadPoolExecutor mit Timeout für den gesamten Scrape-Prozess
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sources_scraper.scrape)
            try:
                # Setze ein striktes Zeitlimit für den gesamten Scrape-Vorgang
                future.result(timeout=MAX_TOTAL_RUNTIME)
            except concurrent.futures.TimeoutError:
                logger.write_to_log(f"Scraper exceeded maximum runtime of {MAX_TOTAL_RUNTIME}s")
            except Exception as e:
                logger.write_to_log(f"Scraper error: {str(e)}")
    except Exception as e:
        logger.write_to_log(f"Critical scraper error: {str(e)}")

    # Berichterstellung über die Laufzeit
    runtime = time.time() - start_time
    logger.write_to_log(f"Total runtime: {runtime:.2f}s for {len(get_sources)} sources")

    # Get the directory path to locate the proxy file
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    # Bereinigung und Ressourcenfreigabe
    del logger
    del helper
    del db
    try:
        del sources_scraper
    except:
        pass
    del sources
    
