"""
Retrieve pending scrapers from the database and terminate specific processes if running for more than 30 minutes.

This function fetches pending scrapers from the database and checks for specific processes running for over 30 minutes to terminate them.

Args:
    None

Returns:
    list: A list of pending scrapers retrieved from the database.
"""

import psutil
import time
import os
import inspect
import json
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime


def get_scrapers_pending():

    """
    Retrieve pending scrapers from the database.

    This function loads the database configuration, connects to the database, and fetches pending sources based on specific criteria.

    Args:
        None

    Returns:
        list: A list of pending scrapers fetched from the database.
    """    

    # Load database configuration from file
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")

    with open(path_db_cnf, encoding="utf-8") as f:
        db_conn = json.load(f)    
    # Connect to the database and fetch pending sources
    conn = psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, progress from scraper where progress = 2")
    conn.commit()
    scraper_pending = cur.fetchall()
    conn.close()
    return scraper_pending

def get_sources_pending():

    """
    Retrieve pending sources from the database.

    This function loads the database configuration, connects to the database, and fetches pending sources based on specific criteria.

    Args:
        None

    Returns:
        list: A list of pending scrapers fetched from the database.
    """    

    # Load database configuration from file
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")

    with open(path_db_cnf, encoding="utf-8") as f:
        db_conn = json.load(f)    
    # Connect to the database and fetch pending sources
    conn = psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT result_source.id, result_source.progress from result_source, source where result_source.source = source.id and result_source.progress = 2")
    conn.commit()
    sources_pending = cur.fetchall()
    conn.close()
    return sources_pending

def get_classifier_pending():

    """
    Retrieve pending sources from the database.

    This function loads the database configuration, connects to the database, and fetches pending sources based on specific criteria.

    Args:
        None

    Returns:
        list: A list of pending scrapers fetched from the database.
    """    

    # Load database configuration from file
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")

    with open(path_db_cnf, encoding="utf-8") as f:
        db_conn = json.load(f)    
    # Connect to the database and fetch pending sources
    conn = psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id from classifier_result where value = 'in process'")
    conn.commit()
    sources_pending = cur.fetchall()
    conn.close()
    return sources_pending

# Retrieve pending scrapers from the database
scrapers_pending = get_scrapers_pending()
sources_pending = get_sources_pending()
classifier_pending = get_classifier_pending()

# Check for pending scrapers and kill specific processes if running for more than 30 minutes
if not scrapers_pending and not sources_pending and not classifier_pending :
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and (
                'chromium' in proc.info['name'] or 
                'chrome' in proc.info['name'] or 
                '--headless=new' in proc.info['cmdline'] or 
                'uc_driver' in proc.info['name'] or 
                'chrome_crashpad_handler' in proc.info['name']
            ):
                etime = time.time() - proc.create_time()
                if etime > 1800: 
                    print(etime)
                    proc.kill()
    except Exception as e:
        print(e)

# Also kill dead drivers when they didn't finish in time (´30 Minutes)
try:
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and (
            'chromium' in proc.info['name'] or 
            'chrome' in proc.info['name'] or 
            '--headless=new' in proc.info['cmdline'] or 
            'uc_driver' in proc.info['name'] or 
            'chrome_crashpad_handler' in proc.info['name']
        ):
            etime = time.time() - proc.create_time()
            if etime > 1800: 
                print(etime)
                proc.kill()
except Exception as e:
    print(e)
