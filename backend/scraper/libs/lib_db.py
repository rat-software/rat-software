import psycopg2
from psycopg2.extras import execute_values
import json

from datetime import datetime

import base64

from bs4 import BeautifulSoup

class DB:

    def __init__(self, db_cnf: dict):
        self.db_cnf = db_cnf

    def __del__(self):
        print('DB Controller object destroyed')

    def connect_to_db(self):
        """
        Connect to the database using psycopg2
        """
        conn =  psycopg2.connect(**self.db_cnf)
        return conn

    def get_scraper_jobs(self):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module FROM scraper, searchengine, query, searchengine_study WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0  ORDER BY scraper.id ASC  LIMIT 2")
        conn.commit()
        scraper_jobs = cur.fetchall()
        conn.close()
        return scraper_jobs

    def update_scraper_job(self, progress, counter, error_code, job_server, scraper_id):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update scraper SET progress=%s, counter=%s, error_code=%s, job_server=%s WHERE id = %s", (progress, counter, error_code, job_server, scraper_id))
        conn.commit()
        conn.close()

    def insert_result(self, title, description, url, position, created_at, main, ip, study, scraper, query, serp):
        """
        Set a placeholder for sources in result table to prevent execution of same source scraper jobs.
        """
        #result: id	title	description	url	position	created_at	main	ip	origin	imported	study	scraper	old_id	resulttype	monitoring	serp	query	final_url
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO result (title, description, url, position, created_at, main, ip, study, scraper, query, serp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (title, description, url, position, created_at, main, ip, study, scraper, query, serp))
        conn.commit()
        conn.close()

    def insert_serp(self, scraper, page, code, img, created_at, query):
        """
        Set a placeholder for sources in result table to prevent execution of same source scraper jobs.
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
        Another checkpoint to verify if a result is already declared as scraping job
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
        Another checkpoint to verify if a result is already declared as scraping job
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


    def check_duplicate_result(self, url, main, study, scraper_id):
        """
        Another checkpoint to verify if a result is already declared as scraping job
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id FROM result WHERE url = %s AND main = %s AND study = %s AND scraper = %s", (url, main, study, scraper_id))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def reset(self):
        """
        Update result_source table when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update scraper SET progress=0 WHERE (progress = -1 OR progress = 2) and counter < 11")
        conn.commit()
        conn.close()
        
    def get_searchengines(self):
        """
        Another checkpoint to verify if a result is already declared as scraping job
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * from searchengine ORDER BY id ASC")
        conn.commit()
        searchengines = cur.fetchall()
        conn.close()   
        return searchengines
    
    def update_searchengine_test(self, se_id, test):     
        """
        Update result_source table when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update searchengine SET test=%s WHERE id = %s", (test, se_id))
        conn.commit()
        conn.close()