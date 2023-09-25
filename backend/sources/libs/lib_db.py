"""
Library for database operations.
"""
#load required libs
import psycopg2
from psycopg2.extras import execute_values
import json
import random
import time
import math
import json
from datetime import datetime

class DB:
    """Database class"""
    db_cnf: dict
    """Dictionary for the database connection"""
    job_server: str
    """Name of the job server"""
    refresh_time: int
    """Hours for refreh scraped sources"""

    def __init__(self, db_cnf: dict, job_server: str, refresh_time: int):
        self.db_cnf = db_cnf
        self.job_server = job_server
        self.refresh_time = refresh_time

    def __del__(self):
        """Destroy Database object"""
        print('DB object destroyed')

    def connect_to_db(self):
        """
        Connect to the database using psycopg2
        """
        conn =  psycopg2.connect(**self.db_cnf)
        return conn

    def insert_result_source(self, result_id, progress, created_at, job_server):
        """
        Set a placeholder for sources in result table to prevent execution of same source scraper jobs.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO result_source (result, progress, created_at, job_server) VALUES (%s, %s, %s, %s);", (result_id, progress, created_at, job_server))
        conn.commit()
        conn.close()


    def get_sources_pending(self):
        """
        Get all failed sources (progress = 2 or progress = -1)
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT source.id, source.created_at, result_source.result from source, result_source where (source.progress = 2 or source.progress = -1) and result_source.source = source.id  and result_source.counter < 11")
        conn.commit()
        sources_pending = cur.fetchall()
        conn.close()
        return sources_pending


    def get_source_check(self, url):
        """
        Read a scraped source by URL
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, created_at from source where progress = 1 and url=%s ORDER by created_at DESC",(url,))
        conn.commit()
        sc = cur.fetchone()
        conn.close()

        #Calculate the time difference of the stored source with the current URL: if the time difference is higher than a specific value (default: 48 hours) scrape the source again; else pass

        if sc:
            timestamp = datetime.now()

            source_id = sc[0]

            created_at = sc[1]

            # Get interval between two timstamps as timedelta object
            diff = timestamp - created_at

            # Get interval between two timstamps in hours
            diff_in_hours = diff.total_seconds() / 3600

            if diff_in_hours < self.refresh_time:
                return source_id
            else:
                return False
        else:
                return False


    def get_source_check_by_result_id(self, result_id):
        """
        Check if a result has already be declared as job to scrape
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id from result_source where result = %s AND progress = 2",(result_id,))
        conn.commit()
        scr = cur.fetchone()
        conn.close()
        return scr

    def get_result_content(self, source_id):
        """
        Get content from an existing result to copy it's content to a source with the same URL
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT result.ip, result.main, result.final_url from result, result_source where result.id = result_source.result and result_source.source =%s",(source_id,))
        conn.commit()
        rc = cur.fetchone()
        conn.close()
        return rc

    def insert_source(self, url, progress, created_at, job_server):
        """
        Insert a new source to the database
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO source (url, progress, created_at, job_server) VALUES (%s, %s, %s, %s)  RETURNING id;", (url, progress, created_at, job_server))
        conn.commit()
        lastrowid = cur.fetchone()
        conn.close()
        return lastrowid

    def check_progress(self, url, result_id):
        """
        Another checkpoint to verify if a result is already declared as scraping job
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT result_source.id FROM result_source, source WHERE result_source.source = source.id AND source.url = %s AND source.progress = 2 AND result_source.result =%s", (url, result_id))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def update_source(self, source_id, code, bin, progress, content_type, error_code, status_code, created_at, content_dict):
        """
        Update source content when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update source SET code=%s, bin=%s, progress=%s, content_type=%s, error_code=%s, status_code=%s, created_at=%s, content_dict = %s WHERE id = %s", (code, bin, progress, content_type, error_code, status_code, created_at, content_dict, source_id))
        conn.commit()
        conn.close()

    def replace_source_bin(self, source_id,  bin):
        """
        Update source content when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update source SET bin=%s WHERE id = %s", (bin, source_id))
        conn.commit()
        conn.close()

    def update_result(self, result_id, ip, main, final_url):
        """
        Update result content when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update result SET ip=%s, main=%s, final_url=%s WHERE id = %s", (ip, main, final_url, result_id))
        conn.commit()
        conn.close()
    
    def get_source_counter_result(self, result_id):
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT counter FROM result_source WHERE result_source.result =%s ", (result_id,))
        conn.commit()
        counter = cur.fetchall()
        conn.close()
        return counter[0][0]


    def update_result_source(self, result_id, source_id, progress, counter, created_at, job_server):
        """
        Update result_source table when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update result_source SET source=%s, progress = %s, counter = %s, created_at =%s, job_server =%s WHERE result = %s", (source_id, progress, counter, created_at, job_server, result_id))
        conn.commit()
        conn.close()
        
    def update_result_source_result(self, result_id, progress, counter, created_at):
        """
        Update result_source table when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update result_source SET progress = %s, counter = %s, created_at =%s WHERE result = %s", (progress, counter, created_at, result_id))
        conn.commit()
        conn.close()

    def delete_source_pending(self, source_id, progress, created_at):
        """
        Delete pending sources
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update source SET progress = %s, created_at =%s WHERE id = %s", (progress, created_at, source_id))
        conn.commit()
        conn.close()

    def reset_result_source(self, progress, counter, created_at, source_id):
        """
        Reset a source in result_source
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update result_source SET progress = %s, counter = %s, created_at =%s WHERE source = %s", (progress, counter, created_at, source_id))
        conn.commit()
        conn.close()



    def reset(self):
        """
        Call reset when the sources_controller stops and delete pending sources
        """
        sources_pending = DB.get_sources_pending(self)
        for sources_pending in sources_pending:
            source_id = sources_pending[0]
            DB.delete_source_pending(self, source_id)
            DB.reset_result_source(self, source_id)

    def get_result_source(self, result_id):
        """
        Check if a result has allready be declared as job to scrape
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id from result_source where result = %s",(result_id,))
        conn.commit()
        scr = cur.fetchone()
        conn.close()
        return scr
    
    def get_result_source_source(self, result_id):
        """
        Check if a result has allready be declared as job to scrape
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT source from result_source where result = %s",(result_id,))
        conn.commit()
        scr = cur.fetchone()
        conn.close()
        return scr[0]

    def get_sources(self, job_server):
        """
        Read all results with no source id (no source_code nor a screenshot)
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        sql = "SELECT result.id, result.url FROM result LEFT JOIN result_source ON result_source.result = result.id WHERE (result_source.source is NULL AND NOT EXISTS (SELECT result from result_source WHERE result = result.id) OR result_source.progress = 0 and result_source.counter < 11)  LIMIT 5"

        cur.execute(sql)
        conn.commit()
        sources = cur.fetchall()
        conn.close()

        sources_list = []

        for s in sources:
            progress = 2
            result_id = s[0]
            result_url = s[1]

            if DB.get_result_source(self, result_id):
                counter = DB.get_source_counter_result(self, result_id)
                counter = counter + 1
                created_at = datetime.now()
                DB.update_result_source_result(self, result_id, progress, counter, created_at)
            else:
                created_at = datetime.now()
                DB.insert_result_source(self, result_id, progress, created_at, job_server)

            sources_list.append([result_id, result_url])


        return sources_list



    def check_db_connection(self):
        """
        Test the database connection
        """
        try:
            conn = DB.connect_to_db(self)
            conn.close()
            return True
        except:
            return False
