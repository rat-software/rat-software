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

    def __init__(self, db_cnf: dict):
        """
        Initialize the DB object with database configuration.

        Args:
            db_cnf (dict): Database configuration dictionary.
        """
        self.db_cnf = db_cnf

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
        Get the classifiers from the database.

        Returns:
            list: List of classifiers with their IDs and names.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT classifier.id, classifier.name, classifier_study.study FROM classifier, classifier_study where classifier.id = classifier_study.classifier")
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

        Args:
            classifier_id (int): ID of the classifier.

        Returns:
            list: List of results for the given classifier ID.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT result.id, result.url, result.main, result.position, result.title, result.description, result.ip, 
                       result.final_url, source.code, source.bin, source.content_type, source.error_code, source.status_code, 
                       result_source.source, classifier_study.classifier
                FROM result, source, result_source, classifier_study
                WHERE result_source.result = result.id AND result_source.source = source.id AND classifier_study.classifier = %s AND result.study = %s
                      AND (source.progress = 1 OR source.progress = -1) 
                      AND result.study = classifier_study.study
                      AND result.id NOT IN (SELECT classifier_result.result FROM classifier_result WHERE classifier_result.classifier = %s)
                ORDER BY result.created_at, result.id
                LIMIT 10 
            """, (classifier_id, study_id, classifier_id))
            conn.commit()
            results = cur.fetchall()
        results = self.get_search_engines(results)
        results = self.get_queries(results)
        return results
    



    def insert_classification_result(self, classifier_id, value, result, job_server):
        """
        Insert a classification result into the database.

        Args:
            classifier_id (int): ID of the classifier.
            value (str): Value of the classification.
            result (int): ID of the result.

        Returns:
            None
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("INSERT INTO classifier_result (classifier, value, result, created_at, job_server) VALUES (%s, %s, %s, %s, %s);", 
                            (classifier_id, value, result, created_at, job_server))
                conn.commit()
        except Exception as e:
            print(f"Error inserting classification result: {e}")

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
            cur.execute("DELETE FROM classifier_result WHERE value = 'in process'", (result,))
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

    def get_results_test(self):
        """
        Get the results for a given classifier ID.

        Args:
            classifier_id (int): ID of the classifier.

        Returns:
            list: List of results for the given classifier ID.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT result.id, result.url, result.main, result.position, result.title, result.description, result.ip, 
                       result.final_url, source.code, source.bin, source.content_type, source.error_code, source.status_code, 
                       result_source.source 
                FROM result, source, result_source 
                WHERE result_source.result = result.id AND result_source.source = source.id 
                      AND (source.progress = 1 OR source.progress = -1)
                      AND result.id = 50585
                      
                ORDER BY result.created_at, result.id 
                LIMIT 10
            """)
            conn.commit()
            results = cur.fetchall()
        return results
