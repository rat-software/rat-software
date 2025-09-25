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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module, searchengine.country, searchengine.resulttype FROM scraper, searchengine, query, searchengine_study, country WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 ORDER BY scraper.id ASC  LIMIT 2")
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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module, searchengine.country, searchengine.resulttype FROM scraper, searchengine, query, searchengine_study, country WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 ORDER BY scraper.id ASC")
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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module, searchengine.country, searchengine.resulttype FROM scraper, searchengine, query, searchengine_study, country  WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 AND scraper.searchengine = %s ORDER BY scraper.id ASC", (searchengine,))
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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module, searchengine.country, searchengine.resulttype  FROM scraper, searchengine, query, searchengine_study, country WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = 0 and counter < 11 AND scraper.searchengine != %s ORDER BY scraper.id ASC  LIMIT 2", (searchengine,))
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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module, searchengine.country, searchengine.resulttype  FROM scraper, searchengine, query, searchengine_study, country  WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND scraper.id = %s ORDER BY scraper.id ASC  LIMIT 2", (job_id,))
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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module, searchengine.country, searchengine.resulttype  FROM scraper, searchengine, query, searchengine_study, country WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = -1 and counter < 11")
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
        cur.execute("SELECT DISTINCT scraper.id AS scraper_id, scraper.searchengine, scraper.study, scraper.counter, scraper.query AS query_id, scraper.limit, query.query, searchengine.module,searchengine.country, searchengine.resulttype FROM scraper, searchengine, query, searchengine_study, country WHERE scraper.searchengine = searchengine.id AND query.id = scraper.query AND searchengine_study.searchengine = searchengine.id AND progress = -1 and counter < 11 and scraper.job_server = %s", (job_server,))
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

    def insert_result(self, title, description, url, position, created_at, main, ip, study, scraper, query, serp, country, normalized_url):
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
        cur.execute("INSERT INTO result (title, description, url, position, created_at, main, ip, study, scraper, query, serp, country, normalized_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (title, description, url, position, created_at, main, ip, study, scraper, query, serp, country, normalized_url))
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


    def check_duplicate_result(self, normalized_url, scraper_id):
        """
        Prüft, ob ein Ergebnis mit derselben normalisierten URL 
        für diesen spezifischen Scraper bereits existiert.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Diese Abfrage ist schnell, erfüllt Ihre Anforderung und vermeidet Typ-Fehler.
        cur.execute(
            "SELECT id FROM result WHERE normalized_url = %s AND scraper = %s",
            (normalized_url, scraper_id)
        )
        
        result_exists = cur.fetchone() is not None
        conn.close()
        return result_exists
            



    def reset(self, job_server):
        """
        Reset the progress of scraper jobs in the database.

        Returns:
            None
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # 1. Bestehende Logik: Setzt hängengebliebene oder fehlgeschlagene Jobs zurück,
        # die noch nicht zu oft versucht wurden (counter < 11).
        cur.execute("Update scraper SET progress=0 WHERE (progress = -1 OR progress = 2) and counter < 11 and created_at < NOW() - INTERVAL '30 minutes' and job_server = %s", (job_server,))

        # 2. NEUE Logik: Setzt den Status auf -1 (endgültig fehlgeschlagen),
        # wenn der Zähler (counter) 10 überschritten hat.
        cur.execute("UPDATE scraper SET progress=-1 WHERE counter > 10")

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

    def check_duplicate_answer(self, study, scraper_id, ai_answer):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id FROM result_ai WHERE answer = %s AND study = %s AND scraper = %s", (ai_answer, study, scraper_id))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def insert_answer(self, study, scraper_id, query_id, ai_answer, ai_answer_html, created_at):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO result_ai (study, scraper, query, answer, answer_html, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;", (study, scraper_id, query_id, ai_answer, ai_answer_html, created_at))
        conn.commit()
        lastrowid = cur.fetchone()
        conn.close()
        return lastrowid[0]
    

    def insert_result_chatbot(self, study, scraper_id, query_id, ai_answer, ai_answer_html, created_at):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO result_chatbot (study, scraper, query, answer, answer_html, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;", (study, scraper_id, query_id, ai_answer, ai_answer_html, created_at))
        conn.commit()
        conn.close()

    def check_duplicate_answer_source(self, answer_id, url, main, study, scraper_id, position):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id FROM result_ai_source WHERE result_ai = %s AND url = %s AND main = %s AND study = %s AND scraper = %s AND position = %s", (answer_id, url, main, study, scraper_id, position))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def insert_answer_source(self, answer_id, title, description, url, position, created_at, main, ip, study, scraper_id, query_id, country, normalized_url):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO result_ai_source (result_ai, title, description, url, position, created_at, main, ip, study, scraper, query, country, normalized_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (answer_id, title, description, url, position, created_at, main, ip, study, scraper_id, query_id, country, normalized_url))
        conn.commit()
        conn.close()



    def get_and_lock_next_scraper_job(self, job_server: str, limit: int = 1, failed_engine_ids: list = None):
        """
        Findet die nächsten offenen Scraper-Jobs, sperrt sie für diesen Prozess
        und gibt sie zurück. Schließt optional als fehlerhaft markierte Suchmaschinen aus.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Basis-SQL, um Jobs zu finden
        sql_find_jobs = "SELECT id FROM scraper WHERE progress = 0 AND counter < 11"
        
        # Parameterliste für die finale Abfrage
        params = []

        # Dynamisches Hinzufügen der Ausschlussbedingung
        if failed_engine_ids:
            sql_find_jobs += " AND searchengine NOT IN %s"
            params.append(tuple(failed_engine_ids)) # Wichtig: psycopg2 erwartet ein Tupel für 'IN'

        sql_find_jobs += " ORDER BY id ASC FOR UPDATE SKIP LOCKED LIMIT %s"
        params.append(limit)
        
        # Finale Abfrage, die die Job-Auswahl als Sub-Query verwendet
        sql_main = f"""
            UPDATE scraper
            SET 
                progress = 2,
                job_server = %s,
                created_at = %s
            WHERE id IN ({sql_find_jobs})
            RETURNING 
                id AS scraper_id, searchengine, study, counter, query AS query_id, 
                "limit", (SELECT query FROM query q WHERE q.id = scraper.query) as query_text, 
                (SELECT module FROM searchengine se WHERE se.id = scraper.searchengine) as module,
                (SELECT country FROM searchengine se WHERE se.id = scraper.searchengine) as country,
                (SELECT resulttype FROM searchengine se WHERE se.id = scraper.searchengine) as resulttype;
        """
        
        # Die Parameter für das UPDATE-Statement an den Anfang der Liste stellen
        update_params = [job_server, datetime.now()]
        final_params = tuple(update_params + params)
        
        try:
            cur.execute(sql_main, final_params)
            locked_jobs = cur.fetchall()
            conn.commit()
            return locked_jobs
        except Exception as e:
            print(f"Fehler beim Sperren von Jobs: {e}")
            conn.rollback()
            return []
        finally:
            conn.close()