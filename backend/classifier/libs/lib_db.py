"""
Database controller class for performing database operations.

Args:
    db_cnf (dict): The database configuration.

Attributes:
    db_cnf (dict): The database configuration.

Methods:
    connect_to_db: Connect to the database using psycopg2.
    get_classifiers: Get the classifiers from the database.
    get_results: Get the results for a given classifier ID.
    insert_classification_result: Insert a classification result into the database.
    insert_indicator: Insert an indicator into the database.
    update_classification_result: Update a classification result in the database.
    reset: Reset the classifiers in the database.
    check_classification_result: Check if a result is already declared as a classification job.
    check_indicator_result: Check if a result is already declared as an indicator job.
    check_source_dup: Check for duplicate sources in the database.
    duplicate_classification_result: Get duplicate classification results for a given source.
    get_classifier_result: Get the classifier result for a given result ID.
    get_indicators: Get the indicators for a given result ID.
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
        Initialize the DB controller object.

        Args:
            db_cnf (dict): The database configuration.
        """        
        self.db_cnf = db_cnf

    def __del__(self):
        """
        Destructor for the DB controller object.
        """        
        print('DB Controller object destroyed')

    def connect_to_db(self):
        """
        Connect to the database using psycopg2.

        Returns:
            psycopg2.extensions.connection: The database connection object.
        """
        conn =  psycopg2.connect(**self.db_cnf)
        return conn

    def get_classifiers(self):
        """
        Get the classifiers from the database.

        Returns:
            list: The list of classifiers.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT classifier.id, classifier.name FROM classifier")
        conn.commit()
        classifiers = cur.fetchall()
        conn.close()
        return classifiers


    def get_results(self, classifier_id):
        """
        Get the results for a given classifier ID.

        Args:
            classifier_id (int): The ID of the classifier.

        Returns:
            list: The list of results.
        """        

        def get_search_engines(results):
            searchengines = []
            conn = DB.connect_to_db(self)
            for result in results:
                result_id = result['id']
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute("SELECT searchengine.name FROM result, scraper, searchengine WHERE result.scraper = scraper.id AND scraper.searchengine = searchengine.id AND result.id = %s", (result_id,))
                conn.commit()
                try:
                    searchengine = cur.fetchone()
                    searchengine = searchengine['name']
                except:
                    searchengine = "N/A"
                result.update({'searchengine': searchengine})
                searchengines.append(result)
            conn.close()
            return searchengines


        def get_queries(results):
            queries = []
            conn = DB.connect_to_db(self)
            for result in results:
                result_id = result['id']
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute("SELECT query.query FROM query, result WHERE result.query = query.id AND result.id = %s", (result_id,))
                conn.commit()
                try:
                    query = cur.fetchone()
                    query = query['query']
                except:
                    query = "N/A"
                result.update({'query': query})
                queries.append(result)
            conn.close()
            return queries

        results_dict = {}
        search_engines = []
        queries = []
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT result.id, result.url, result.main, result.position, result.title, result.description, result.ip, result.final_url, source.code, source.bin, source.content_type, source.error_code, source.status_code, result_source.source FROM result, source, result_source, classifier_study WHERE result.study = classifier_study.study AND classifier_study.classifier = %s AND result_source.result = result.id AND result_source.source = source.id AND (source.progress = 1 OR source.progress = -1) AND result.id NOT IN (SELECT classifier_result.result FROM classifier_result where classifier_result.classifier = %s) ORDER BY result.created_at, result.id LIMIT 10" , (classifier_id, classifier_id))
        conn.commit()
        results = cur.fetchall()
        results = get_search_engines(results)
        results = get_queries(results)

        conn.close()
        return results


    def insert_classification_result(self, classifier_id, value, result):
        """
        Insert a classification result into the database.

        Args:
            classifier_id (int): The ID of the classifier.
            value (str): The value of the classification result.
            result (int): The ID of the result.

        Returns:
            None
        """       
        try:
            created_at = datetime.now()
            conn = DB.connect_to_db(self)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("INSERT INTO classifier_result (classifier, value, result, created_at) VALUES (%s, %s, %s, %s);", (classifier_id, value, result, created_at))
            conn.commit()
            conn.close()
        except:
            pass

    def insert_indicator(self, indicator, value, classifier_id, result):
        """
        Insert an indicator into the database.

        Args:
            indicator (str): The indicator.
            value (str): The value of the indicator.
            classifier_id (int): The ID of the classifier.
            result (int): The ID of the result.

        Returns:
            None
        """        
        try:
            created_at = datetime.now()
            conn = DB.connect_to_db(self)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("INSERT INTO classifier_indicator (indicator, value, classifier, result, created_at) VALUES (%s, %s, %s, %s, %s);", (indicator, value, classifier_id, result, created_at))
            conn.commit()
            conn.close()
        except:
            pass

    def update_classification_result(self, classifier_id, value, result):
        """
        Update a classification result in the database.

        Args:
            classifier_id (int): The ID of the classifier.
            value (str): The value of the classification result.
            result (int): The ID of the result.

        Returns:
            None
        """        
        try:
            created_at = datetime.now()
            conn = DB.connect_to_db(self)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("UPDATE classifier_result SET classifier=%s, value=%s, created_at=%s WHERE result = %s", (classifier_id, value, created_at, result))
            conn.commit()
            conn.close()

        except:
            pass



    def reset(self):

        def reset_classifiers(result):
            """
            Reset the classifiers for a given result.

            Args:
                result (int): The ID of the result.

            Returns:
                None
            """            
            conn = DB.connect_to_db(self)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("DELETE FROM classifier_indicator WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE value = 'in process'", (result,))
            conn.commit()
            conn.close()

        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT classifier_indicator.result FROM classifier_indicator, classifier_result WHERE classifier_indicator.result NOT IN (SELECT classifier_result.result FROM classifier_result) GROUP BY classifier_indicator.result")
        conn.commit()
        values = cur.fetchall()
        for v in values:
            result = v['result']
            reset_classifiers(result)
        conn.close()

    def check_classification_result(self, classifier, result):
        """
        Check if a result is already declared as a scraping job.

        Args:
            classifier (int): The ID of the classifier.
            result (int): The ID of the result.

        Returns:
            bool: True if the result is already declared, False otherwise.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id FROM classifier_result WHERE classifier = %s AND result = %s AND value !='in process'", (classifier, result))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def check_indicator_result(self, classifier, result):
        """
        Check if a result is already declared as a classifier job.

        Args:
            classifier (int): The ID of the classifier.
            result (int): The ID of the result.

        Returns:
            bool: True if the result is already declared, False otherwise.
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id FROM classifier_indicator WHERE classifier = %s AND result = %s", (classifier, result))
        conn.commit()
        check_progress = cur.fetchall()
        conn.close()
        if check_progress:
            return True
        else:
            return False

    def check_source_dup(self, source):
        """
        Check for duplicate sources in the database.

        Args:
            source (int): The ID of the source.

        Returns:
            list: The list of duplicate sources.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM result_source WHERE source = %s", (source,))
        conn.commit()
        check_source = cur.fetchall()
        conn.close()
        return check_source

    def duplicate_classification_result(self, source):
        """
        Get duplicate classification results for a given source.

        Args:
            source (int): The ID of the source.

        Returns:
            list: The list of duplicate classification results.
        """        

        def get_results_result_source(source):
            conn = DB.connect_to_db(self)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT result FROM result_source WHERE source = %s", (source,))
            conn.commit()
            result_sources = cur.fetchall()
            conn.close()
            return result_sources

        result_sources = get_results_result_source(source)
        return result_sources

    def get_classifier_result(self, result):
        """
        Get the classifier result for a given result ID.

        Args:
            result (int): The ID of the result.

        Returns:
            list: The list of classifier results.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT value FROM classifier_result WHERE result = %s and value !='in process'", (result,))
        conn.commit()
        result_sources = cur.fetchall()
        conn.close()
        return result_sources

    def get_indicators(self, result):
        """
        Get the indicators for a given result ID.

        Args:
            result (int): The ID of the result.

        Returns:
            list: The list of indicators.
        """        
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM classifier_indicator WHERE result = %s", (result,))
        conn.commit()
        result_indicators = cur.fetchall()
        conn.close()
        return result_indicators
