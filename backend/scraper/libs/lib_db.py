"""
Database class for interacting with the database.

Args:
    db_cnf (dict): Dictionary containing the database configuration.

Methods:
    __init__: Initialize the DB object.
    __del__: Destructor for the DB object.
    connect_to_db: Connect to the database using psycopg2.
    get_scraper_jobs: Get scraper jobs from the database.
    update_scraper_job: Update the progress of a scraper job in the database.
    insert_result: Insert a result into the database.
    insert_serp: Insert a SERP (Search Engine Results Page) into the database.
    check_progress: Check if a result is already declared as a scraping job.
    check_scraper_progress: Check if a scraper job is already in progress.
    check_duplicate_result: Check if a result with the same URL, main, study, and scraper ID already exists.
    reset: Reset the progress of scraper jobs in the database.
    get_searchengines: Get the list of search engines from the database.
    update_searchengine_test: Update the test field of a search engine in the database.
"""

import psycopg2
from psycopg2.extras import execute_values
import json

from datetime import datetime

import base64

from bs4 import BeautifulSoup

class DB:
    def __init__(self, db_cnf: dict):
        """
        Initialize the DB object.

        Args:
            db_cnf (dict): Dictionary containing the database configuration.
        """        
        self.db_cnf = db_cnf

    def __del__(self):
        """
        Destructor for the DB object.
        """        
        print('DB Controller object destroyed')

    def connect_to_db(self):
        """
        Connect to the database using psycopg2
        """
        conn =  psycopg2.connect(**self.db_cnf)
        return conn

    def get_scraper_jobs(self):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 and scraper.study > 17 ORDER BY scraper.id ASC  LIMIT 2")
        conn.commit()
        scraper_jobs = cur.fetchall()
        conn.close()
        return scraper_jobs
    
    def get_all_open_scraper_jobs(self):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 and scraper.study > 17 ORDER BY scraper.id ASC")
        conn.commit()
        scraper_jobs = cur.fetchall()
        conn.close()
        return scraper_jobs    
    
    def get_scraper_jobs_searchengine(self, searchengine):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 AND scraper.searchengine = %s and scraper.study > 17 ORDER BY scraper.id ASC", (searchengine,))
        conn.commit()
        scraper_jobs = cur.fetchall()
        conn.close()
        return scraper_jobs    
    
    def get_scraper_jobs_filter_searchengine(self, searchengine):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 and scraper.study > 17 AND scraper.searchengine != %s ORDER BY scraper.id ASC  LIMIT 2", (searchengine,))
        conn.commit()
        scraper_jobs = cur.fetchall()
        conn.close()
        return scraper_jobs     
    
    
    def get_scraper_job(self, job_id):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND scraper.id = %s and scraper.study > 12 ORDER BY scraper.id ASC  LIMIT 2", (job_id,))
        conn.commit()
        scraper_jobs = cur.fetchall()
        conn.close()
        return scraper_jobs    

    def get_failed_scraper_jobs(self):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = -1 and counter < 11 and scraper.study > 12")
        conn.commit()
        failed_scraper_jobs = cur.fetchall()
        conn.close()
        return failed_scraper_jobs
    
    def get_failed_scraper_jobs_server(self, job_server):
        """
        Get scraper jobs from the database.

        Returns:
            list: List of scraper jobs.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = -1 and counter < 11 and scraper.job_server = %s", (job_server,))
        conn.commit()
        failed_scraper_jobs = cur.fetchall()
        conn.close()
        return failed_scraper_jobs    

    def update_scraper_job(self, progress, counter, error_code, job_server, scraper_id, created_at):
        """
        Update the progress of a scraper job in the database.

        Args:
            progress (int): Progress value.
            counter (int): Counter value.
            error_code (str): Error code.
            job_server (str): Job server.
            scraper_id (int): Scraper ID.

        Returns:
            None
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update scraper SET progress=%s, counter=%s, error_code=%s, job_server=%s, created_at=%s WHERE id = %s", (progress, counter, error_code, job_server, created_at, scraper_id))
        conn.commit()
        conn.close()

    def insert_result(self, title, description, url, position, created_at, main, ip, study, scraper, query, serp):
        """
        Insert a result into the database.

        Args:
            title (str): Title of the result.
            description (str): Description of the result.
            url (str): URL of the result.
            position (int): Position of the result.
            created_at (datetime): Creation timestamp of the result.
            main (bool): Flag indicating if it's a main result.
            ip (str): IP address of the result.
            study (int): Study ID.
            scraper (int): Scraper ID.
            query (int): Query ID.
            serp (int): SERP ID.

        Returns:
            None
        """
        #result: id	title	description	url	position	created_at	main	ip	origin	imported	study	scraper	old_id	resulttype	monitoring	serp	query	final_url
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO result (title, description, url, position, created_at, main, ip, study, scraper, query, serp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (title, description, url, position, created_at, main, ip, study, scraper, query, serp))
        conn.commit()
        conn.close()

    def insert_serp(self, scraper, page, code, img, created_at, query):
        """
        Insert a SERP (Search Engine Results Page) into the database.

        Args:
            scraper (int): Scraper ID.
            page (int): Page number.
            code (str): Code of the SERP.
            img (str): Image of the SERP.
            created_at (datetime): Creation timestamp of the SERP.
            query (int): Query ID.

        Returns:
            int: ID of the inserted SERP.
        """
        #serp id	scraper	page	code	img	progress	created_at	old_id	monitoring	query
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id from serp where scraper = %s and page = %s and query = %s",(scraper, page, query,))
        conn.commit()
        serp = cur.fetchone()

        if not serp:
            cur.execute("INSERT INTO serp (scraper, page, code, img, created_at, query) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;", (scraper, page, code, img, created_at, query))
            conn.commit()
            serp = cur.fetchone()

        conn.close()
        return serp

    def check_progress(self, study, query_id):
        """
        Check if a result is already declared as a scraping job.

        Args:
            study (int): Study ID.
            query_id (int): Query ID.

        Returns:
            bool: True if the progress is 2, False otherwise.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT scraper.id FROM scraper WHERE study = %s AND query = %s AND progress = 2", (study, query_id))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def check_scraper_progress(self, scraper_id):
        """
        Check if a scraper job is already in progress.

        Args:
            scraper_id (int): Scraper ID.

        Returns:
            bool: True if the progress is 2, False otherwise.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT scraper.id FROM scraper WHERE id = %s AND progress = 2", (scraper_id,))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False


    def check_duplicate_result(self, url, main, study, scraper_id, position):
        """
        Check if a result with the same URL, main, study, and scraper ID already exists.

        Args:
            url (str): URL of the result.
            main (bool): Flag indicating if it's a main result.
            study (int): Study ID.
            scraper_id (int): Scraper ID.

        Returns:
            bool: True if a duplicate result exists, False otherwise.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id FROM result WHERE url = %s AND main = %s AND study = %s AND scraper = %s AND position = %s", (url, main, study, scraper_id, position))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def reset(self, job_server):
        """
        Reset the progress of scraper jobs in the database.

        Returns:
            None
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update scraper SET progress=0 WHERE (progress = -1 OR progress = 2) and counter < 11 and created_at < NOW() - INTERVAL '30 minutes' and job_server = %s", (job_server,))
        conn.commit()
        conn.close()
        
    def get_searchengines(self):
        """
        Get the list of search engines from the database.

        Returns:
            list: List of search engines.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * from searchengine ORDER BY id ASC")
        conn.commit()
        searchengines = cur.fetchall()
        conn.close()   
        return searchengines

    def get_failed_searchengines(self):
        """
        Get the list of search engines from the database.

        Returns:
            list: List of search engines.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * from searchengine WHERE test = -1 ORDER BY id ASC")
        conn.commit()
        searchengines = cur.fetchall()
        conn.close()   
        return searchengines
    
    def update_searchengine_test(self, se_id, test):     
        """
        Update the test field of a search engine in the database.

        Args:
            se_id (int): Search engine ID.
            test (str): Test value.

        Returns:
            None
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update searchengine SET test=%s WHERE id = %s", (test, se_id))
        conn.commit()
        conn.close()

    def get_range_study(self, study):
        """
        Get the list of result ranges for the study.

        Returns:
            list: list with result ranges.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT range_start, range_end from range_study WHERE study = %s ORDER BY id ASC", (study,))
        conn.commit()
        searchengines = cur.fetchall()
        conn.close()   
        return searchengines