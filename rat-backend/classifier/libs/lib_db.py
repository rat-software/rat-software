import psycopg2
from psycopg2.extras import execute_values, RealDictCursor, DictCursor
from datetime import datetime

class DB:
    """
    Database class to handle various database operations.

    Attributes:
        db_cnf (dict): Dictionary containing database configuration.
    """
    db_cnf: dict

    def __init__(self, db_cnf: dict, job_server: str = "unknown_server", refresh_time: int = 48, max_counter: int = 3):
        """
        Initialize the DB object with database configuration.

        Args:
            db_cnf (dict): Database configuration dictionary.
            job_server (str): Identifier of the processing server.
            refresh_time (int): Refresh interval.
            max_counter (int): Maximum retry counter for dead sources.
        """
        self.db_cnf = db_cnf
        self.job_server = job_server
        self.refresh_time = refresh_time
        self.max_counter = max_counter

    def __del__(self):
        """Destroy Database object and print a message."""
        print('DB object destroyed')

    def connect_to_db(self):
        """
        Context manager for database connection.

        Returns:
            ConnectionManager: A context manager for database connections.
        """
        class ConnectionManager:
            def __init__(self, db_cnf):
                self.db_cnf = db_cnf
                self.conn = None

            def __enter__(self):
                self.conn = psycopg2.connect(**self.db_cnf)
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.conn:
                    self.conn.close()

        return ConnectionManager(self.db_cnf)
    

    def get_classifiers(self):
        """
        Get the classifiers from the database, but ONLY for studies that
        actually have pending results or dead sources to flag.
        This completely eliminates the bottleneck of iterating through old, finished studies.
        """
        from psycopg2.extras import RealDictCursor
        
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # The EXISTS clause acts like a high-speed radar. 
            # It only returns the classifier/study combo if there is at least ONE 
            # row that actually requires processing by the Python script.
            cur.execute("""
                SELECT classifier.id, classifier.name, classifier_study.study 
                FROM classifier
                JOIN classifier_study ON classifier.id = classifier_study.classifier
                WHERE EXISTS (
                    SELECT 1 
                    FROM result
                    JOIN result_source ON result_source.result = result.id
                    JOIN source ON result_source.source = source.id
                    LEFT JOIN classifier_result cr ON cr.result = result.id AND cr.classifier = classifier.id
                    WHERE result.study = classifier_study.study
                      AND (
                          -- Condition 1: Fresh, unclassified sources
                          (source.progress = 1 AND cr.id IS NULL)
                          OR
                          -- Condition 2: Dead sources that need the 'source_failed' flag
                          (source.progress = -1 AND result_source.counter >= %s AND (cr.value IS NULL OR cr.value IN ('error', 'classifier_error', 'in process')))
                      )
                )
                ORDER BY classifier_study.study DESC
            """, (self.max_counter,))
            
            conn.commit()
            classifiers = cur.fetchall()
            
        return classifiers

    def get_search_engines(self, results):
        """
        Get search engines for results.

        Args:
            results (list): List of results.

        Returns:
            list: Updated list of results with search engines.
        """
        with self.connect_to_db() as conn:
            for result in results:
                result_id = result['id']
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT searchengine.name FROM result, scraper, searchengine WHERE result.scraper = scraper.id AND scraper.searchengine = searchengine.id AND result.id = %s", (result_id,))
                conn.commit()
                searchengine = cur.fetchone()
                result['searchengine'] = searchengine['name'] if searchengine else "N/A"
        return results

    def get_queries(self, results):
        """
        Get queries for results.

        Args:
            results (list): List of results.

        Returns:
            list: Updated list of results with queries.
        """
        with self.connect_to_db() as conn:
            for result in results:
                result_id = result['id']
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT query.query FROM query, result WHERE result.query = query.id AND result.id = %s", (result_id,))
                conn.commit()
                query = cur.fetchone()
                result['query'] = query['query'] if query else "N/A"
        return results

    def get_results(self, classifier_id, study_id):     
        """
        Get the results for a given classifier ID.
        Only feeds fully successful scrapes (progress = 1) to the classifiers.
        """
        from psycopg2.extras import RealDictCursor
        
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT DISTINCT ON (result.id)
                       result.id, result.url, result.main, result.position, result.title, result.description, result.ip, 
                       result.final_url, source.file_path, source.content_type, source.error_code, source.status_code, 
                       result_source.source, classifier_study.classifier
                FROM result
                JOIN result_source ON result_source.result = result.id
                JOIN source ON result_source.source = source.id
                JOIN classifier_study ON result.study = classifier_study.study
                LEFT JOIN classifier_result cr ON cr.result = result.id AND cr.classifier = %s
                WHERE classifier_study.classifier = %s 
                  AND result.study = %s
                  AND source.progress = 1 
                  AND cr.id IS NULL
                ORDER BY result.id, result.created_at
                LIMIT 10
            """, (classifier_id, classifier_id, study_id))
            
            conn.commit()
            results = cur.fetchall()
            
        # Assuming you have these helper functions elsewhere in your class
        if hasattr(self, 'get_search_engines'):
            results = self.get_search_engines(results)
        if hasattr(self, 'get_queries'):
            results = self.get_queries(results)
            
        return results

    def insert_classification_result(self, classifier_id, value, result, job_server):
        """
        Insert a classification result into the database.
        Returns True if successfully locked, False if another instance beat us to it.
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("INSERT INTO classifier_result (classifier, value, result, created_at, job_server) VALUES (%s, %s, %s, %s, %s);", 
                            (classifier_id, value, result, created_at, job_server))
                conn.commit()
            return True # Sperre erfolgreich gesetzt!
        except Exception as e:
            # '23505' ist der standardisierte PostgreSQL-Fehlercode für unique_violation
            if hasattr(e, 'pgcode') and e.pgcode == '23505':
                return False # Ein anderer Worker war schneller, sauber abbrechen ohne Crash
            
            print(f"Error inserting classification result: {e}")
            return False

    def insert_indicator(self, indicator, value, classifier_id, result, job_server):
        """
        Insert an indicator into the database.

        Args:
            indicator (str): Indicator name.
            value (str): Value of the indicator.
            classifier_id (int): ID of the classifier.
            result (int): ID of the result.

        Returns:
            None
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("INSERT INTO classifier_indicator (indicator, value, classifier, result, created_at, job_server) VALUES (%s, %s, %s, %s, %s, %s);", 
                            (indicator, value, classifier_id, result, created_at, job_server))
                conn.commit()
        except Exception as e:
            print(f"Error inserting indicator: {e}")

    def update_classification_result(self, value, result_id, classifier_id):
        """
        Update a classification result in the database.

        Args:
            classifier_id (int): ID of the classifier.
            value (str): Updated value of the classification.
            result (int): ID of the result.

        Returns:
            None
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("UPDATE classifier_result SET value=%s, created_at=%s WHERE result = %s and classifier_result.classifier =%s", 
                            (value, created_at, result_id, classifier_id))
                conn.commit()
        except Exception as e:
            print(f"Error updating classification result: {e}")

    def reset_classifiers(self, result):
        """
        Reset the classifiers for a given result.

        Args:
            result (int): ID of the result.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("DELETE FROM classifier_indicator WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE value = 'in process' AND result = %s", (result,))
            conn.commit()

    def reset(self, job_server):
        """
       Reset any unfinished classifiers in the database if not all indicators could be resolved.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT classifier_indicator.result FROM classifier_indicator, classifier_result WHERE classifier_indicator.job_server = %s AND classifier_indicator.result NOT IN (SELECT classifier_result.result FROM classifier_result) GROUP BY classifier_indicator.result", (job_server,))
            conn.commit()
            values = cur.fetchall()
        for v in values:
            result = v['result']
            self.reset_classifiers(result)

    def check_classification_result(self, classifier, result):
        """
        Check if a result is already declared as a scraping job.

        Args:
            classifier (int): ID of the classifier.
            result (int): ID of the result.

        Returns:
            bool: True if the result is already declared, False otherwise.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT id FROM classifier_result WHERE classifier = %s AND result = %s", 
                        (classifier, result))
            conn.commit()
            check_progress = cur.fetchall()
        return bool(check_progress)
    
    def check_classification_result_not_in_process(self, classifier, result):
        """
        Check if a result is already declared as a scraping job.

        Args:
            classifier (int): ID of the classifier.
            result (int): ID of the result.

        Returns:
            bool: True if the result is already declared, False otherwise.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT id FROM classifier_result WHERE classifier = %s AND result = %s AND value !='in process'", 
                        (classifier, result))
            conn.commit()
            check_progress = cur.fetchall()
        return check_progress

    def check_indicator_result(self, classifier, result, indicator, value):
        """
        Check if a result is already declared as a classifier job.

        Args:
            classifier (int): ID of the classifier.
            result (int): ID of the result.

        Returns:
            bool: True if the result is already declared, False otherwise.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT id FROM classifier_indicator WHERE classifier = %s AND result = %s AND indicator = %s AND value = %s", 
                        (classifier, result , indicator, value))
            conn.commit()
            check_progress = cur.fetchall()
        return bool(check_progress)

    def check_source_duplicates(self, source):
        """
        Check for duplicate sources in the database.

        Args:
            source (int): ID of the source.

        Returns:
            list: List of duplicate sources.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT * FROM result_source WHERE source = %s", (source,))
            conn.commit()
            check_source = cur.fetchall()
        return check_source

    def get_results_result_source(self, source):
        """
        Get results for a given source.

        Args:
            source (int): ID of the source.

        Returns:
            list: List of results for the given source.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT result FROM result_source WHERE source = %s", (source,))
            conn.commit()
            result_ids = cur.fetchall()
        return result_ids

    def get_classifier_result(self, result):
        """
        Get the classifier result for a given result ID.

        Args:
            result (int): ID of the result.

        Returns:
            list: List of classifier results for the given result ID.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT value FROM classifier_result WHERE result = %s and value !='in process'", 
                        (result,))
            conn.commit()
            result_sources = cur.fetchall()
        return result_sources

    def get_indicators(self, result):
        """
        Get the indicators for a given result ID.

        Args:
            result (int): ID of the result.

        Returns:
            list: List of indicators for the given result ID.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT * FROM classifier_indicator WHERE result = %s", (result,))
            conn.commit()
            result_indicators = cur.fetchall()
        return result_indicators

    def deleteClassifierDuplicates(self):
        """
        Delete duplicate classifier results.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("""
                DELETE FROM classifier_result 
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (PARTITION BY result, classifier_result.classifier ORDER BY id) AS row_num 
                        FROM classifier_result
                    ) t WHERE t.row_num > 1
                );
            """)
            conn.commit()


    def flag_dead_sources(self, classifier_id, study_id, job_server):
        """
        Central method: Finds all results whose source permanently failed 
        (progress = -1 and counter >= self.max_counter) and marks them in 
        classifier_result as 'source_failed'.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT result.id, cr.id as cr_id 
                FROM result
                JOIN result_source ON result_source.result = result.id
                JOIN source ON result_source.source = source.id
                LEFT JOIN classifier_result cr ON cr.result = result.id AND cr.classifier = %s
                WHERE result.study = %s
                  AND source.progress = -1 
                  AND result_source.counter >= %s
                  AND (cr.value IS NULL OR cr.value IN ('error', 'classifier_error', 'in process'))
            """, (classifier_id, study_id, self.max_counter))
            
            dead_results = cur.fetchall()
            
        # Register the final failure for all found dead sources
        for row in dead_results:
            result_id = row['id']
            if row['cr_id']:
                self.update_classification_result('source_failed', result_id, classifier_id)
            else:
                self.insert_classification_result(classifier_id, 'source_failed', result_id, job_server)            

    def check_db_connection(self):
        """
        Test the database connection.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            with self.connect_to_db():
                return True
        except Exception as e:
            print(f"Error checking DB connection: {e}")
            return False