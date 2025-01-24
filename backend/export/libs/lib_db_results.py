# Load required libraries
import psycopg2
from psycopg2.extras import execute_values
import json
import random
import time
import math
from datetime import datetime

class DB:
    """Database interaction class for managing and querying a PostgreSQL database."""
    
    db_cnf: dict
    """Dictionary containing the database connection configuration."""
    
    job_server: str
    """Name of the job server that is processing the data."""
    
    refresh_time: int
    """Time in hours to refresh scraped sources."""

    def __init__(self, db_cnf: dict, job_server: str, refresh_time: int):
        """
        Initializes the DB object with the given database configuration, job server, and refresh time.

        Args:
            db_cnf (dict): Dictionary containing database configuration details.
            job_server (str): Name of the job server.
            refresh_time (int): Time in hours to refresh scraped sources.
        """
        self.db_cnf = db_cnf
        self.job_server = job_server
        self.refresh_time = refresh_time

    def __del__(self):
        """Destructor for the DB object, prints a message when the object is destroyed."""
        print('DB object destroyed')

    def connect_to_db(self):
        """
        Establishes a connection to the PostgreSQL database using psycopg2.

        Returns:
            psycopg2.extensions.connection: Database connection object.
        """
        conn = psycopg2.connect(**self.db_cnf)
        return conn

    def insert_result_source(self, result_id, progress, created_at, job_server):
        """
        Inserts a placeholder entry into the result_source table to track sources and avoid duplicate scraping jobs.

        Args:
            result_id (int): ID of the result.
            progress (int): Progress status of the scraping job.
            created_at (datetime): Timestamp when the entry was created.
            job_server (str): Job server name.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            INSERT INTO result_source (result, progress, created_at, job_server) 
            VALUES (%s, %s, %s, %s);
        """, (result_id, progress, created_at, job_server))
        conn.commit()
        conn.close()

    def get_sources_pending(self):
        """
        Retrieves sources that have failed (progress = 2 or progress = -1) and have not exceeded retry limit.

        Returns:
            list: List of dictionaries containing failed sources with their details.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT source.id, source.created_at, result_source.result 
            FROM source
            JOIN result_source ON result_source.source = source.id 
            WHERE (source.progress = 2 OR source.progress = -1) 
              AND result_source.counter < 11
        """)
        conn.commit()
        sources_pending = cur.fetchall()
        conn.close()
        return sources_pending

    def get_source_check(self, url):
        """
        Checks if a source with the specified URL exists and if it should be refreshed based on its creation time.

        Args:
            url (str): URL of the source.

        Returns:
            int or bool: Source ID if the source should be refreshed, otherwise False.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, created_at 
            FROM source 
            WHERE progress = 1 AND url = %s 
            ORDER BY created_at DESC
        """, (url,))
        conn.commit()
        sc = cur.fetchone()
        conn.close()

        if sc:
            timestamp = datetime.now()
            source_id = sc[0]
            created_at = sc[1]
            diff = timestamp - created_at
            diff_in_hours = diff.total_seconds() / 3600

            if diff_in_hours < self.refresh_time:
                return source_id
            else:
                return False
        else:
            return False

    def get_source_check_by_result_id(self, result_id):
        """
        Checks if a result has already been declared as a scraping job.

        Args:
            result_id (int): ID of the result.

        Returns:
            tuple or None: Source ID if a scraping job is declared, otherwise None.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id 
            FROM result_source 
            WHERE result = %s AND progress = 2
        """, (result_id,))
        conn.commit()
        scr = cur.fetchone()
        conn.close()
        return scr

    def get_result_content(self, source_id):
        """
        Retrieves content from an existing result associated with the specified source.

        Args:
            source_id (int): ID of the source.

        Returns:
            tuple: Content details of the associated result.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT result.ip, result.main, result.final_url 
            FROM result
            JOIN result_source ON result_source.result = result.id
            WHERE result_source.source = %s
        """, (source_id,))
        conn.commit()
        rc = cur.fetchone()
        conn.close()
        return rc

    def insert_source(self, url, progress, created_at, job_server):
        """
        Inserts a new source into the database.

        Args:
            url (str): URL of the source.
            progress (int): Progress status of the source.
            created_at (datetime): Timestamp when the source was created.
            job_server (str): Job server name.

        Returns:
            int: ID of the newly inserted source.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            INSERT INTO source (url, progress, created_at, job_server) 
            VALUES (%s, %s, %s, %s)  
            RETURNING id;
        """, (url, progress, created_at, job_server))
        conn.commit()
        lastrowid = cur.fetchone()[0]
        conn.close()
        return lastrowid

    def check_progress(self, url, result_id):
        """
        Checks if a result is already declared as a scraping job for the given URL.

        Args:
            url (str): URL of the source.
            result_id (int): ID of the result.

        Returns:
            bool: True if the result is already declared, otherwise False.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT result_source.id 
            FROM result_source
            JOIN source ON result_source.source = source.id 
            WHERE source.url = %s 
              AND source.progress = 2 
              AND result_source.result = %s
        """, (url, result_id))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        return bool(check_progress)

    def update_source(self, source_id, code, bin, progress, content_type, error_code, status_code, created_at, content_dict):
        """
        Updates the content of a source when the scraping job is completed.

        Args:
            source_id (int): ID of the source to be updated.
            code (int): HTTP response code.
            bin (bytearray): Binary content of the source.
            progress (int): Progress status of the source.
            content_type (str): MIME type of the content.
            error_code (int): Error code if any.
            status_code (int): Status code of the request.
            created_at (datetime): Timestamp when the source was created.
            content_dict (dict): Additional content details.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE source 
            SET code = %s, bin = %s, progress = %s, content_type = %s, 
                error_code = %s, status_code = %s, created_at = %s, content_dict = %s 
            WHERE id = %s
        """, (code, bin, progress, content_type, error_code, status_code, created_at, content_dict, source_id))
        conn.commit()
        conn.close()

    def replace_source_bin(self, source_id, bin):
        """
        Updates the binary content of a source when the scraping job is completed.

        Args:
            source_id (int): ID of the source to be updated.
            bin (bytearray): New binary content for the source.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE source 
            SET bin = %s 
            WHERE id = %s
        """, (bin, source_id))
        conn.commit()
        conn.close()

    def update_result(self, result_id, ip, main, final_url):
        """
        Updates the result content when the scraping job is completed.

        Args:
            result_id (int): ID of the result to be updated.
            ip (str): IP address associated with the result.
            main (str): Main content of the result.
            final_url (str): Final URL after scraping.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE result 
            SET ip = %s, main = %s, final_url = %s 
            WHERE id = %s
        """, (ip, main, final_url, result_id))
        conn.commit()
        conn.close()

    def get_source_counter_result(self, result_id):
        """
        Retrieves the counter value for a result from the result_source table.

        Args:
            result_id (int): ID of the result.

        Returns:
            int: Counter value associated with the result.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT counter 
            FROM result_source 
            WHERE result = %s
        """, (result_id,))
        conn.commit()
        counter = cur.fetchall()
        conn.close()
        return counter[0][0]

    def update_result_source(self, result_id, source_id, progress, counter, created_at, job_server):
        """
        Updates the result_source table with new details for a scraping job.

        Args:
            result_id (int): ID of the result.
            source_id (int): ID of the source.
            progress (int): Progress status of the scraping job.
            counter (int): Counter value for the result.
            created_at (datetime): Timestamp when the entry was created.
            job_server (str): Name of the job server.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE result_source 
            SET source = %s, progress = %s, counter = %s, created_at = %s, job_server = %s 
            WHERE result = %s
        """, (source_id, progress, counter, created_at, job_server, result_id))
        conn.commit()
        conn.close()

    def update_result_source_result(self, result_id, progress, counter, created_at):
        """
        Updates the result_source table with new details for a result.

        Args:
            result_id (int): ID of the result.
            progress (int): Progress status of the scraping job.
            counter (int): Counter value for the result.
            created_at (datetime): Timestamp when the entry was created.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE result_source 
            SET progress = %s, counter = %s, created_at = %s 
            WHERE result = %s
        """, (progress, counter, created_at, result_id))
        conn.commit()
        conn.close()

    def delete_source_pending(self, source_id, progress, created_at):
        """
        Deletes or updates pending sources that have not yet completed.

        Args:
            source_id (int): ID of the source to be updated.
            progress (int): New progress status of the source.
            created_at (datetime): Timestamp when the entry was created.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE source 
            SET progress = %s, created_at = %s 
            WHERE id = %s
        """, (progress, created_at, source_id))
        conn.commit()
        conn.close()

    def reset_result_source(self, progress, counter, created_at, source_id):
        """
        Resets the result_source entry for a source.

        Args:
            progress (int): New progress status of the source.
            counter (int): New counter value for the result.
            created_at (datetime): Timestamp when the entry was created.
            source_id (int): ID of the source to be reset.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        created_at = datetime.now()
        cur.execute("""
            UPDATE result_source 
            SET progress = %s, counter = %s, created_at = %s 
            WHERE source = %s
        """, (progress, counter, created_at, source_id))
        conn.commit()
        conn.close()

    def reset(self):
        """
        Resets all pending sources by deleting or updating them and resetting result_source entries.
        """
        sources_pending = self.get_sources_pending()
        for source in sources_pending:
            source_id = source[0]
            self.delete_source_pending(source_id, source[1], source[2])
            self.reset_result_source(source[1], source[2], source[2], source_id)

    def get_result_source(self, result_id):
        """
        Retrieves the result_source entry for a given result ID.

        Args:
            result_id (int): ID of the result.

        Returns:
            tuple: Result source entry if exists, otherwise None.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id 
            FROM result_source 
            WHERE result = %s
        """, (result_id,))
        conn.commit()
        scr = cur.fetchone()
        conn.close()
        return scr

    def get_result_source_source(self, result_id):
        """
        Retrieves the source ID for a given result ID.

        Args:
            result_id (int): ID of the result.

        Returns:
            int: Source ID associated with the result.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT source 
            FROM result_source 
            WHERE result = %s
        """, (result_id,))
        conn.commit()
        scr = cur.fetchone()
        conn.close()
        return scr[0]

    def get_sources(self, job_server):
        """
        Retrieves results that do not have an associated source and are eligible for scraping.

        Args:
            job_server (str): Name of the job server requesting the sources.

        Returns:
            list: List of tuples containing result IDs and URLs that are ready for scraping.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT result.id, result.url, study.studytype 
            FROM result
            JOIN study ON result.study = study.id
            LEFT JOIN result_source ON result_source.result = result.id
            WHERE (result_source.source IS NULL 
                AND NOT EXISTS (SELECT result FROM result_source WHERE result = result.id) 
                OR result_source.progress = 0 
                AND result_source.counter < 11) 
              AND study.studytype != 6 
            LIMIT 5
        """)
        conn.commit()
        sources = cur.fetchall()
        conn.close()

        sources_list = []

        for s in sources:
            progress = 2
            result_id = s[0]
            result_url = s[1]

            if self.get_result_source(result_id):
                counter = self.get_source_counter_result(result_id)
                counter += 1
                created_at = datetime.now()
                self.update_result_source_result(result_id, progress, counter, created_at)
            else:
                created_at = datetime.now()
                self.insert_result_source(result_id, progress, created_at, job_server)

            sources_list.append([result_id, result_url])

        return sources_list

    def check_db_connection(self):
        """
        Tests the connection to the database to ensure it is active.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            conn = self.connect_to_db()
            conn.close()
            return True
        except:
            return False
