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
        """

        #initialize an event based dictionary for the scraping results
        result_dict_available = threading.Event()      

        def scrape_url(sources_url, proxy, country_code, timeout=450):
            """Thread-sicherer URL-Scraper mit Timeout"""
            global result_dict  
            result_dict = None
            
            try:
                self.logger.write_to_log(f"Starting scrape for URL: {sources_url} with timeout {timeout}s")
                start_time = time.time()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.sources.save_code, sources_url, proxy, country_code)
                    
                    try:
                        result_dict = future.result(timeout=timeout)
                        elapsed = time.time() - start_time
                        self.logger.write_to_log(f"Scraping completed for {sources_url} in {elapsed:.2f}s")
                    except concurrent.futures.TimeoutError as te:
                        error_msg = f"Scraping timed out after {timeout}s for URL: {sources_url}"
                        self.logger.write_to_log(error_msg)
                        result_dict = {
                            "file_path": None, 
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
                            "file_path": None, 
                            "request": {"content_type": "error", "status_code": -1},
                            "final_url": sources_url,
                            "meta": {"ip": "-1", "main": sources_url},
                            "error_codes": error_msg,
                            "content_dict": {"":""}
                        }
                if result_dict is None:
                    self.logger.write_to_log(f"No result returned for {sources_url} - creating default error result")
                    result_dict = {
                        "file_path": None, 
                        "request": {"content_type": "error", "status_code": -1},
                        "final_url": sources_url,
                        "meta": {"ip": "-1", "main": sources_url},
                        "error_codes": error_msg,
                        "content_dict": {"":""}
                    }
            except Exception as outer_e:
                self.logger.write_to_log(f"Critical error in scrape_url function: {str(outer_e)}")
                result_dict = {
                    "file_path": None, 
                    "request": {"content_type": "error", "status_code": -1},
                    "final_url": sources_url,
                    "meta": {"ip": "-1", "main": sources_url},
                    "error_codes": "Critical worker error",
                    "content_dict": {"":""}
                }
            finally:
                elapsed = time.time() - start_time
                self.logger.write_to_log(f"Setting result available for {sources_url} after {elapsed:.2f}s")
                result_dict_available.set()


        #loop through all sources to scrape
        for source_to_scrape in self.get_sources:
            global result_dict
            result_dict = None
            
            result_id = source_to_scrape[0] 
            url = source_to_scrape[1] 
            country_proxy = source_to_scrape[2] 
            country_code = source_to_scrape[3] 
   
            # ====================================================================
            # NEU: SOFORTIGES EXTRAHIEREN UND SPEICHERN DER MAIN DOMAIN
            # ====================================================================
            # Dadurch ist die Domain immer für die Analyse-Seite verfügbar,
            # selbst wenn der Scraper bei dieser URL komplett abstürzt!
            base_main = url
            base_ip = "-1"
            try:
                # Wir nutzen die Hilfsfunktion aus lib_sources rein zum Parsen
                base_meta = self.sources.get_result_meta(url)
                base_main = base_meta.get("main", url)
                base_ip = base_meta.get("ip", "-1")
                
                # Sofortiger DB-Eintrag!
                self.db.update_result(result_id, base_ip, base_main, url)
            except Exception as e:
                self.logger.write_to_log(f"Fehler beim initialen Parsen der URL {url}: {e}")
            # ====================================================================

            try:
                proxy, proxy_error = get_proxy_for_scraping(country_proxy, self.country)
            except Exception as e:
                proxy = None
                proxy_error = f"Proxy selection failed: {str(e)}"
                self.logger.write_to_log(f"Critical proxy error: {proxy_error}")
            
            if proxy_error:
                log = f"Proxy error for {country_proxy}: {proxy_error}"
                self.logger.write_to_log(log)
                         
            progress = 2 
            created_at = datetime.now() 
            content_dict = {"":""}
            counter = 1  
            source_id = None  
            
            if self.db.check_progress(url, result_id):
                self.logger.write_to_log(f"Skipping {url} (ID: {result_id}) - already in progress")
                continue
            else:
                try:
                    source_id_check = self.db.get_source_check(url, country_proxy) 

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
                            created_at = datetime.now()
                            print("new")
                            print(source_id)
                            self.db.update_result_source(result_id, source_id, 2, counter, created_at, self.job_server)
                        else:
                            source_id = False

                        if source_id: 
                            try:
                                try:
                                    counter = self.db.get_source_counter_result(result_id)
                                except Exception as e:
                                    self.logger.write_to_log(f"Error getting counter for result {result_id}: {str(e)}")
                                    counter = 1
                                
                                if country_proxy != self.country and country_proxy is not None and proxy is None:
                                    error_code = f"No working proxies available for {country_proxy}: {proxy_error}"
                                    progress = -1
                                    status_code = -1
                                    error = "error"
                                    log = f"{source_id}_{result_id}\t{url}\t{progress}\t{error_code}"
                                    self.logger.write_to_log(log)
                                    created_at = datetime.now()
                                    self.db.update_source(source_id, None, progress, error, error_code, status_code, created_at, content_dict)                                    
                                    self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server)
                                    continue

                                max_scrape_time = 450  
                                start_time = time.time()
                                
                                thread = threading.Thread(target=scrape_url, args=(url, proxy, country_code, max_scrape_time))
                                thread.daemon = True  
                                thread.start()

                                wait_timeout = max_scrape_time * 1.5  
                                wait_start_time = time.time()
                                
                                while not result_dict_available.is_set():
                                    result_dict_available.wait(5)
                                    elapsed = time.time() - wait_start_time
                                    if elapsed > wait_timeout:
                                        self.logger.write_to_log(f"Timeout waiting for result from {url} after {elapsed:.2f}s")
                                        break
                                    if int(elapsed) % 60 == 0:
                                        self.logger.write_to_log(f"Still waiting for result from {url} ({elapsed:.2f}s elapsed)")
                                    if result_dict is not None:
                                        self.logger.write_to_log(f"Result available for {url} after {elapsed:.2f}s")
                                        break
                                
                                if result_dict is None:
                                    self.logger.write_to_log(f"Result dict not available for {url} after {time.time() - wait_start_time:.2f}s")
                                    result_dict = {
                                        "file_path": None, 
                                        "request": {"content_type": "error", "status_code": -1},
                                        "final_url": url,
                                        "meta": {"ip": "-1", "main": url},
                                        "error_codes": "Result unavailable after waiting",
                                        "content_dict": {"":""}
                                    }
                                    
                                result_dict_available.clear()

                                file_path = result_dict.get('file_path')
                                content_type = result_dict.get('request', {}).get('content_type', "error") 
                                status_code = result_dict.get('request', {}).get('status_code', -1) 
                                final_url = result_dict.get('final_url', url) 
                                ip = result_dict.get('meta', {}).get('ip', "-1") 
                                main = result_dict.get('meta', {}).get('main', url) 
                                error_code = result_dict.get('error_codes', "") 
                                
                                # NEU: Wenn der Scraper wegen Timeout abstürzt, gibt er als "main" oft 
                                # einfach wieder die Roh-URL zurück. Wir fangen das ab und verwenden 
                                # unsere saubere base_main Domain!
                                if main == url or main == final_url:
                                    main = base_main
                                if ip == "-1":
                                    ip = base_ip

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

                                if (status_code != 200 or 
                                    content_type == 'error' or 
                                    file_path is None or  
                                    has_timeout):
                                    progress = -1
                                else:
                                    progress = 1

                                log_msg = f"Progress set to {progress} for {url}: status={status_code}, content_type={content_type}"
                                if progress == -1:
                                    reasons = []
                                    if status_code != 200:
                                        reasons.append(f"status_code is {status_code} (not 200)")
                                    if content_type == 'error':
                                        reasons.append("content_type is error")
                                    if has_timeout:
                                        reasons.append(f"timeout detected: '{error_code}'")
                                    
                                    log_msg += ", reasons: " + ", ".join(reasons)
                                self.logger.write_to_log(log_msg)

                                if len(final_url) == 0:
                                    final_url = url

                                try:
                                    self.db.update_source(
                                            source_id, 
                                            file_path, 
                                            progress, 
                                            content_type, 
                                            error_code, 
                                            status_code, 
                                            created_at, 
                                            content_dict
                                        ) 
                                    created_at = datetime.now()
                                    self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server)
                                    
                                    # Das 2. Update der Result Tabelle, falls sich durch einen Redirect die URL/Domain geändert hat
                                    self.db.update_result(result_id, ip, main, final_url)

                                except Exception as e:
                                    self.logger.write_to_log("Updating source table failed \t \t \t"+str(e))
                                    log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                    self.logger.write_to_log(log)

                                    print(str(e))
                                    proxy_info = f" (Proxy: {proxy})" if proxy else ""
                                    if proxy_error:
                                        proxy_info += f" Proxy issues: {proxy_error}"
                                    
                                    error_code = f"Source Controller scraping failed: {str(e)}{proxy_info}" 
                                    error = "error"
                                    progress = -1
                                    status_code = -1
                                    content_dict = "error"
                                    log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                    created_at = datetime.now()
                                    self.logger.write_to_log(log)
                                    self.db.update_source(source_id, None, progress, error, error_code, status_code, created_at, content_dict)
                                    self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) 

                            except Exception as e:
                                try:
                                    counter = self.db.get_source_counter_result(result_id)
                                except:
                                    counter = 1
                                
                                proxy_info = f" (Proxy: {proxy})" if proxy else ""
                                if proxy_error:
                                    proxy_info += f" Proxy issues: {proxy_error}"
                                    
                                error_code = f"Final Source Controller scraping failed: {str(e)}{proxy_info}"
                                print(error_code)
                                error = "error"
                                progress = -1
                                status_code = -1
                                log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                                created_at = datetime.now() 
                                self.logger.write_to_log(log)
                                self.db.update_source(source_id, None, progress, error, error_code, status_code, created_at, content_dict)                                
                                self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) 

                except Exception as e:
                    proxy_info = f" (Proxy: {proxy})" if proxy else ""
                    if proxy_error:
                        proxy_info += f" Proxy issues: {proxy_error}"
                        
                    error_code = f"Process failed Source Controller scraping failed: {str(e)}{proxy_info}" 
                    print(error_code)
                    error = "error"
                    progress = -1
                    status_code = -1
                    content_dict = "error"  
                    log = "Skipped Result:"+str(result_id)+"\t"+str(e)+"\t \t \t "
                    self.logger.write_to_log(log)
                    if source_id:  
                        self.db.update_source(source_id, None, progress, error, error_code, status_code, created_at, content_dict) 
                        created_at = datetime.now() 
                        self.db.update_result_source(result_id, source_id, progress, counter, created_at, self.job_server) 

if __name__ == "__main__":
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

    try:
        get_sources = db.get_sources(job_server) 
        if not get_sources:
            print("No sources to scrape found.")
            logger.write_to_log("No sources to scrape found")
            del logger
            del helper
            del db
            del sources
            sys.exit(0)
    except Exception as e:
        print(f"Error getting sources: {str(e)}")
        logger.write_to_log(f"Error getting sources: {str(e)}")
        del logger
        del helper
        del db
        del sources
        sys.exit(1)

    print(get_sources)

    MAX_TOTAL_RUNTIME = 7200  
    start_time = time.time()

    sources_scraper = SourcesScraper(get_sources, job_server, db, logger, sources, country) 
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sources_scraper.scrape)
            try:
                future.result(timeout=MAX_TOTAL_RUNTIME)
            except concurrent.futures.TimeoutError:
                logger.write_to_log(f"Scraper exceeded maximum runtime of {MAX_TOTAL_RUNTIME}s")
            except Exception as e:
                logger.write_to_log(f"Scraper error: {str(e)}")
    except Exception as e:
        logger.write_to_log(f"Critical scraper error: {str(e)}")

    runtime = time.time() - start_time
    logger.write_to_log(f"Total runtime: {runtime:.2f}s for {len(get_sources)} sources")

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    del logger
    del helper
    del db
    try:
        del sources_scraper
    except:
        pass
    del sources