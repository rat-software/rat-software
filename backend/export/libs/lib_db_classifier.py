import psycopg2
from psycopg2.extras import execute_values, RealDictCursor, DictCursor
from datetime import datetime

class DB:
    """Database interaction class for managing and querying a PostgreSQL database."""
    
    def __init__(self, db_cnf: dict):
        """
        Initializes the DB object with the given database configuration.

        Args:
            db_cnf (dict): Dictionary containing database configuration details.
        """
        self.db_cnf = db_cnf

    def __del__(self):
        """Destructor for the DB object."""
        print('DB object destroyed')

    def connect_to_db(self):
        """
        Provides a context manager for managing database connections.

        Returns:
            ConnectionManager: A context manager for handling the database connection.
        """
        class ConnectionManager:
            def __init__(self, db_cnf):
                self.db_cnf = db_cnf
                self.conn = None

            def __enter__(self):
                """Establishes a database connection."""
                self.conn = psycopg2.connect(**self.db_cnf)
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                """Closes the database connection."""
                if self.conn:
                    self.conn.close()

        return ConnectionManager(self.db_cnf)

    def get_classifiers(self):
        """
        Retrieves all classifiers from the database.

        Returns:
            list: A list of classifiers with their IDs and names.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT classifier.id, classifier.name FROM classifier")
            conn.commit()
            classifiers = cur.fetchall()
        return classifiers

    def get_search_engines(self, results):
        """
        Retrieves the search engines associated with the given results.

        Args:
            results (list): A list of results, each represented as a dictionary.

        Returns:
            list: The updated list of results with search engine names added.
        """
        with self.connect_to_db() as conn:
            for result in results:
                result_id = result['id']
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT searchengine.name 
                    FROM result
                    JOIN scraper ON result.scraper = scraper.id
                    JOIN searchengine ON scraper.searchengine = searchengine.id
                    WHERE result.id = %s
                """, (result_id,))
                conn.commit()
                searchengine = cur.fetchone()
                result['searchengine'] = searchengine['name'] if searchengine else "N/A"
        return results

    def get_queries(self, results):
        """
        Retrieves the queries associated with the given results.

        Args:
            results (list): A list of results, each represented as a dictionary.

        Returns:
            list: The updated list of results with queries added.
        """
        with self.connect_to_db() as conn:
            for result in results:
                result_id = result['id']
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT query.query 
                    FROM query
                    JOIN result ON result.query = query.id
                    WHERE result.id = %s
                """, (result_id,))
                conn.commit()
                query = cur.fetchone()
                result['query'] = query['query'] if query else "N/A"
        return results

    def get_results(self, classifier_id):
        """
        Retrieves results for a specific classifier ID.

        Args:
            classifier_id (int): The ID of the classifier for which to retrieve results.

        Returns:
            list: A list of results for the specified classifier.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT result.id, result.url, result.main, result.position, result.title, 
                       result.description, result.ip, result.final_url, source.code, 
                       source.bin, source.content_type, source.error_code, source.status_code, 
                       result_source.source 
                FROM result
                JOIN source ON result_source.source = source.id
                JOIN result_source ON result_source.result = result.id
                JOIN classifier_study ON result.study = classifier_study.study
                WHERE classifier_study.classifier = %s
                  AND (source.progress = 1 OR source.progress = -1)
                  AND result.id NOT IN (
                      SELECT classifier_result.result 
                      FROM classifier_result 
                      WHERE classifier_result.classifier = %s
                  )
                ORDER BY result.created_at, result.id 
                LIMIT 10
            """, (classifier_id, classifier_id))
            conn.commit()
            results = cur.fetchall()
        
        # Enrich results with search engine and query information
        results = self.get_search_engines(results)
        results = self.get_queries(results)
        return results

    def insert_classification_result(self, classifier_id, value, result):
        """
        Inserts a classification result into the database.

        Args:
            classifier_id (int): The ID of the classifier.
            value (str): The classification result value.
            result (int): The ID of the result being classified.

        Returns:
            None
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("""
                    INSERT INTO classifier_result (classifier, value, result, created_at) 
                    VALUES (%s, %s, %s, %s);
                """, (classifier_id, value, result, created_at))
                conn.commit()
        except Exception as e:
            print(f"Error inserting classification result: {e}")

    def insert_indicator(self, indicator, value, classifier_id, result):
        """
        Inserts an indicator into the database.

        Args:
            indicator (str): The indicator name.
            value (str): The value of the indicator.
            classifier_id (int): The ID of the classifier.
            result (int): The ID of the result.

        Returns:
            None
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("""
                    INSERT INTO classifier_indicator (indicator, value, classifier, result, created_at) 
                    VALUES (%s, %s, %s, %s, %s);
                """, (indicator, value, classifier_id, result, created_at))
                conn.commit()
        except Exception as e:
            print(f"Error inserting indicator: {e}")

    def update_classification_result(self, classifier_id, value, result):
        """
        Updates a classification result in the database.

        Args:
            classifier_id (int): The ID of the classifier.
            value (str): The updated classification result value.
            result (int): The ID of the result being updated.

        Returns:
            None
        """
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("""
                    UPDATE classifier_result 
                    SET classifier=%s, value=%s, created_at=%s 
                    WHERE result = %s
                """, (classifier_id, value, created_at, result))
                conn.commit()
        except Exception as e:
            print(f"Error updating classification result: {e}")

    def reset_classifiers(self, result):
        """
        Resets the classifiers for a given result by deleting related entries.

        Args:
            result (int): The ID of the result to reset classifiers for.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("DELETE FROM classifier_indicator WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE value = 'in process'", (result,))
            conn.commit()

    def reset(self):
        """
        Resets the classifiers in the database by cleaning up orphaned classifier indicators.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT classifier_indicator.result 
                FROM classifier_indicator
                LEFT JOIN classifier_result ON classifier_indicator.result = classifier_result.result
                WHERE classifier_result.result IS NULL
                GROUP BY classifier_indicator.result
            """)
            conn.commit()
            values = cur.fetchall()
        
        for v in values:
            result = v['result']
            self.reset_classifiers(result)

    def check_classification_result(self, classifier, result):
        """
        Checks if a classification result for a given result ID and classifier ID already exists.

        Args:
            classifier (int): The ID of the classifier.
            result (int): The ID of the result.

        Returns:
            bool: True if the result is classified; False otherwise.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("""
                SELECT id 
                FROM classifier_result 
                WHERE classifier = %s AND result = %s AND value != 'in process'
            """, (classifier, result))
            conn.commit()
            check_progress = cur.fetchall()
        return bool(check_progress)

    def check_indicator_result(self, classifier, result):
        """
        Checks if an indicator result for a given result ID and classifier ID already exists.

        Args:
            classifier (int): The ID of the classifier.
            result (int): The ID of the result.

        Returns:
            bool: True if the indicator result exists; False otherwise.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("""
                SELECT id 
                FROM classifier_indicator 
                WHERE classifier = %s AND result = %s
            """, (classifier, result))
            conn.commit()
            check_progress = cur.fetchall()
        return bool(check_progress)

    def check_source_dup(self, source):
        """
        Checks for duplicate sources in the database.

        Args:
            source (int): The ID of the source to check for duplicates.

        Returns:
            list: List of duplicate source entries.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT * FROM result_source WHERE source = %s", (source,))
            conn.commit()
            check_source = cur.fetchall()
        return check_source

    def duplicate_classification_result(self, source):
        """
        Retrieves duplicate classification results for a given source.

        Args:
            source (int): The ID of the source.

        Returns:
            list: List of duplicate classification results.
        """
        return self.get_results_result_source(source)

    def get_results_result_source(self, source):
        """
        Retrieves results associated with a given source.

        Args:
            source (int): The ID of the source.

        Returns:
            list: List of result IDs associated with the source.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT result FROM result_source WHERE source = %s", (source,))
            conn.commit()
            result_sources = cur.fetchall()
        return result_sources

    def get_classifier_result(self, result):
        """
        Retrieves the classification result for a given result ID.

        Args:
            result (int): The ID of the result.

        Returns:
            list: List of classification results for the given result.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("""
                SELECT value 
                FROM classifier_result 
                WHERE result = %s AND value != 'in process'
            """, (result,))
            conn.commit()
            result_sources = cur.fetchall()
        return result_sources

    def get_indicators(self, result):
        """
        Retrieves indicators associated with a given result ID.

        Args:
            result (int): The ID of the result.

        Returns:
            list: List of indicators for the given result.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT * FROM classifier_indicator WHERE result = %s", (result,))
            conn.commit()
            result_indicators = cur.fetchall()
        return result_indicators

    def deleteClassifierDuplicates(self):
        """
        Deletes duplicate classification results based on result ID.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("""
                DELETE FROM classifier_result 
                WHERE id IN (
                    SELECT id 
                    FROM (
                        SELECT id, ROW_NUMBER() OVER(PARTITION BY result ORDER BY id) AS row_num 
                        FROM classifier_result
                    ) t 
                    WHERE t.row_num > 1
                );
            """)
            conn.commit()

    def check_db_connection(self):
        """
        Tests the database connection by attempting to connect.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            with self.connect_to_db():
                return True
        except Exception as e:
            print(f"Error checking DB connection: {e}")
            return False
