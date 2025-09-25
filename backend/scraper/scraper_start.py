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
from libs.lib_scraping_ai import Scraping_AI
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode

TRACKING_PARAMS_TO_REMOVE = [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'dclid', 'fbclid', '_hsenc', '_hsmi', 'mkt_tok', 'msclkid',
    'mc_cid', 'mc_eid', 'trk', 'onwewe'
]

def normalize_url(url: str) -> str:
    """
    Eine verbesserte Normalisierungsfunktion, die:
    1. Bekannte Tracking-Parameter entfernt.
    2. Das Schema auf HTTPS vereinheitlicht.
    3. Die 'www.'-Subdomain entfernt.
    4. Einen Schrägstrich am Ende des Pfades entfernt.
    """
    if not isinstance(url, str) or not url.strip():
        return ""
    
    try:
        parts = urlsplit(url)
        query_params = parse_qs(parts.query, keep_blank_values=True)
        
        filtered_params = {
            key: value for key, value in query_params.items() 
            if key.lower() not in TRACKING_PARAMS_TO_REMOVE
        }
        new_query = urlencode(filtered_params, doseq=True)

        # Schema auf 'https' vereinheitlichen
        scheme = 'https'
        
        # 'www.' aus der Domain entfernen
        netloc = parts.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
            
        # Schrägstrich am Ende des Pfades entfernen
        path = parts.path
        if path != '/' and path.endswith('/'):
            path = path[:-1]

        # URL neu zusammensetzen
        return urlunsplit((scheme, netloc, path, new_query, parts.fragment))
    except Exception as e:
        print(f"Warnung: Konnte URL nicht normalisieren: {url}. Fehler: {e}")
        return url

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
            country = scraper_job['country']

            print(country)

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
                    
                    if scraping_results == 0:  # Neue Bedingung für "keine Ergebnisse gefunden" Nachricht
                        progress = 1  # Erfolgreicher Abschluss
                        error_code = 0
                        print("No results found message detected - marking as completed")
                        db.update_scraper_job(progress, counter, error_code, job_server, scraper_id, scraper_job_created_at)
                    elif scraping_results and scraping_results != -1:
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
                            normalized_url = normalize_url(url)
                            serp_id = None                             
                            
                            if position <= limit:
                                if ranges:
                                    if position in ranges:
                                        if not db.check_duplicate_result(normalized_url, scraper_id):
                                            #serp = db.insert_serp(scraper_id, page, code, img, created_at, query_id)
                                            db.insert_result(title, description, url, position, created_at, main, ip, study, scraper_id, query_id, serp_id, country, normalized_url)

                                else:
                                    if not db.check_duplicate_result(normalized_url, scraper_id):
                                        #serp = db.insert_serp(scraper_id, page, code, img, created_at, query_id)
                                        db.insert_result(title, description, url, position, created_at, main, ip, study, scraper_id, query_id, serp_id, country, normalized_url)
                           
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

    def scrape_ai(self, scraper_jobs, db: DB, scraping: Scraping, job_server: str):
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
            country = scraper_job['country']
            created_at = datetime.now()

            print(country)

            if not db.check_progress(study, query_id):
                continue

            try:
                #if db.check_scraper_progress(scraper_id):
                print("Start Scraping")
                time.sleep(1)  # Sleep to avoid potential race conditions
                scraper_module = importlib.import_module(mod_folder)
                scraping_results = scraper_module.run(query, limit, scraping, True)

                if scraping_results and scraping_results != -1:
                    progress = 1  # Indicates successful completion
                    error_code = 0 # Reset error code
                    serp = [""] 


                    ai_answer = scraping_results[0]
                    ai_answer_html = scraping_results[1]
                    ai_sources = scraping_results[2]
                    position = 0

                    if not db.check_duplicate_answer(study, scraper_id, ai_answer):
                        answer_id = db.insert_answer(study, scraper_id, query_id, ai_answer, ai_answer_html, created_at)

                        for ai_source in ai_sources:
                            position += 1
                            title = ai_source['title']
                            description = ai_source['description']
                            url = ai_source['href']
                            meta = scraping.get_result_meta(url)
                            ip = meta['ip']
                            main = meta['main']
                            created_at = datetime.now()
                            normalized_url = normalize_url(url)

                            if not db.check_duplicate_answer_source(answer_id, url, main, study, scraper_id, position):
                                print(url)    
                                db.insert_answer_source(answer_id, title, description, url, position, created_at, main, ip, study, scraper_id, query_id, country, normalized_url)
                                    
                        print("Success:"+str(error_code))
                            
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


    def scrape_chatbot(self, scraper_jobs, db: DB, scraping: Scraping, job_server: str):
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
            country = scraper_job['country']
            created_at = datetime.now()

            print(country)

            if not db.check_progress(study, query_id):
                continue

            try:
                #if db.check_scraper_progress(scraper_id):
                print("Start Scraping")
                time.sleep(1)  # Sleep to avoid potential race conditions
                scraper_module = importlib.import_module(mod_folder)
                scraping_results = scraper_module.run(query, limit, scraping, True)

                if scraping_results and scraping_results != -1:
                    progress = 1  # Indicates successful completion
                    error_code = 0 # Reset error code
                    serp = [""] 


                    ai_answer = scraping_results[0]
                    ai_answer_html = scraping_results[1]
 
                    if not db.check_duplicate_answer(study, scraper_id, ai_answer):
                        db.insert_result_chatbot(study, scraper_id, query_id, ai_answer, ai_answer_html, created_at)

    
                        print("Success:"+str(error_code))
                            
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

    # Konfigurationen laden
    db_cnf = os.path.join(currentdir, "../config/config_db.ini")
    helper = Helper()
    db_cnf = helper.file_to_dict(db_cnf)
    db = DB(db_cnf)

    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
    sources_cnf = helper.file_to_dict(path_sources_cnf)
    job_server = sources_cnf['job_server']

    # 1. Fehlerhafte Suchmaschinen ermitteln
    failed_scraper_jobs = db.get_failed_scraper_jobs_server(job_server)
    failed_se_counts = {}
    for fs in failed_scraper_jobs:
        se_id = fs['searchengine']
        failed_se_counts[se_id] = failed_se_counts.get(se_id, 0) + 1
    
    failed_search_engines = [
        se_id for se_id, count in failed_se_counts.items() if count > 9
    ]
    if failed_search_engines:
        print(f"Schließe folgende Suchmaschinen wegen zu vieler Fehler aus: {failed_search_engines}")

    # 2. Die nächsten X freien Jobs holen und atomar sperren
    scraper_jobs_to_process = db.get_and_lock_next_scraper_job(
        job_server, 
        limit=5, # Wir holen uns z.B. 5 Jobs auf einmal
        failed_engine_ids=failed_search_engines
    )

    if not scraper_jobs_to_process:
        print("Keine offenen Scraper-Jobs gefunden.")
    else:
        # 3. Jobs nach ihrem Typ gruppieren
        jobs_by_type = {1: [], 2: [], 4: []}
        for sj in scraper_jobs_to_process:
            # Spalte 'query_text' in 'query' umbenennen für Kompatibilität
            sj['query'] = sj.pop('query_text')
            resulttype = sj.get("resulttype")
            if resulttype in jobs_by_type:
                jobs_by_type[resulttype].append(sj)

        # 4. Die jeweiligen Scrape-Methoden nur einmal pro Job-Typ aufrufen
        scraper = Scraper()
        scraping_instance = Scraping() # Nur einmal erstellen

        if jobs_by_type[1]:
            print(f"Starte {len(jobs_by_type[1])} normale Scraping-Jobs...")
            scraper.scrape(jobs_by_type[1], db, scraping_instance, job_server)
        
        if jobs_by_type[2]:
            print(f"Starte {len(jobs_by_type[2])} AI-Scraping-Jobs...")
            scraper.scrape_ai(jobs_by_type[2], db, scraping_instance, job_server)
        
        if jobs_by_type[4]:
            print(f"Starte {len(jobs_by_type[4])} Chatbot-Scraping-Jobs...")
            scraper.scrape_chatbot(jobs_by_type[4], db, scraping_instance, job_server)
        
        del scraper

    # Ressourcen aufräumen
    del helper
    del db