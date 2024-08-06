"""
Script to manage and clean up processes and database entries related to the scraping application.

This script performs the following tasks:
1. Terminates specific running processes based on their command-line arguments.
2. Updates the database by removing obsolete classifier results and resetting pending sources.

Dependencies:
    - psutil: For managing and killing processes.
    - time: For time-related operations (though not used directly in this script).
    - os: For interacting with the operating system, including file path operations.
    - sys: For system-specific parameters and functions (though not used directly in this script).
    - inspect: For inspecting live objects and obtaining the current file's directory.
    - json: For parsing the database configuration file.
    - psycopg2: For PostgreSQL database connection and operations.
"""

import psutil
import os
import json
import psycopg2
import inspect
from psycopg2.extras import DictCursor, RealDictCursor

def load_db_config(config_path):
    """
    Load the database configuration from a JSON file.

    Args:
        config_path (str): Path to the JSON configuration file.

    Returns:
        dict: Database configuration parameters.
    """
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def terminate_processes(args:list):
    """
    Terminate specific processes based on their command-line arguments.

    Processes are terminated if their command-line arguments contain specific keywords.
    """
    kill_browser = True
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
         
            if proc.info['cmdline']:
                for cmd in proc.info['cmdline']:
                    if any(keyword in cmd for keyword in ['sources', 'classifier', 'scraper', 'chrome_controller']):
                        if '.py' in cmd:
                            try:
                                print(f"Terminating process with PID {proc.info['pid']}: {cmd}")
                                proc.kill()
                                kill_browser = True
                            except:
                                pass                

            #Kill browser processes specified in the arguments
            if kill_browser:
                for browser in args:
                    if proc.info['cmdline'] and proc.info['name']:
                        if browser in proc.info['name'] or browser in proc.info['cmdline']:
                            proc.kill()
                           
                                                     
    
    except Exception as e:
        print("Error terminating processes:", str(e))

def reset_classifiers(result, db_conn, job_server):
    """
    Reset classifier-related entries for a specific result in the database.

    Args:
        result (str): Identifier of the result to reset.
        db_conn (dict): Database connection parameters.
    """
    with psycopg2.connect(**db_conn) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("DELETE FROM classifier_indicator WHERE result = %s and job_server = %s", (result, job_server))
            cur.execute("DELETE FROM classifier_result WHERE result = %s and job_server = %s", (result, job_server))
            cur.execute("DELETE FROM classifier_result WHERE value = 'in process'  and job_server = %s", (job_server,))
            conn.commit()

def update_pending_jobs(db_conn, job_server):
    """
    Update pending jobs in the database by resetting progress status and removing obsolete entries.
    
    Args:
        db_conn (dict): Database connection parameters.
    """
    # Reset progress of scraper jobs
    with psycopg2.connect(**db_conn) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("UPDATE scraper SET progress = 0 WHERE progress = -1 OR progress = 2 and job_server = %s", (job_server,))
            conn.commit()

    # Remove obsolete classifier results
    with psycopg2.connect(**db_conn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT classifier_indicator.result
                FROM classifier_indicator
                LEFT JOIN classifier_result ON classifier_indicator.result = classifier_result.result
                WHERE classifier_result.result IS NULL
                GROUP BY classifier_indicator.result
            """)
            obsolete_results = cur.fetchall()
            for record in obsolete_results:
                result = record['result']
                reset_classifiers(result, db_conn, job_server)

def get_sources_pending(db_conn, job_server):
    """
    Retrieve all sources with pending status (progress = 2) from the database.

    Args:
        db_conn (dict): Database connection parameters.

    Returns:
        list: List of tuples containing source ID and creation timestamp.
    """
    with psycopg2.connect(**db_conn) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT id, created_at FROM source WHERE progress = 2 and job_server = %s", (job_server,))
            return cur.fetchall()

def delete_source_pending(source_id, db_conn, job_server):
    """
    Delete a source entry from the database based on its ID.

    Args:
        source_id (int): Identifier of the source to delete.
        db_conn (dict): Database connection parameters.
    """
    with psycopg2.connect(**db_conn) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("DELETE FROM source WHERE id = %s and job_server = %s", (source_id, job_server))
            conn.commit()

def reset_result_source(source_id, db_conn, job_server):
    """
    Remove entries from the result_source table related to a specific source ID.

    Args:
        source_id (int): Identifier of the source to reset.
        db_conn (dict): Database connection parameters.
    """
    with psycopg2.connect(**db_conn) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("DELETE FROM result_source WHERE source = %s and job_server = %s", (source_id, job_server))
            conn.commit()

if __name__ == "__main__":
    # Load database configuration
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    path_db_cnf = os.path.join(currentdir, "config", "config_db.ini")
    db_conn = load_db_config(path_db_cnf)

    path_sources_cnf = os.path.join(currentdir, "config", "config_sources.ini")

    # Open the JSON file for reading with UTF-8 encoding
    with open(path_sources_cnf, encoding="utf-8") as f:
            # Load the JSON content into a dictionary
        data = json.load(f)
    
    job_server = data['job_server']
    
    # Terminate specific processes
    terminate_processes(["chromium", "chrome", "--headless=new", "uc_driver"])

    # Update pending jobs and reset results
    update_pending_jobs(db_conn, job_server)

    # Reset sources
    sources_pending = get_sources_pending(db_conn, job_server)
    for source in sources_pending:
        source_id = source['id']
        reset_result_source(source_id, db_conn, job_server)
        delete_source_pending(source_id, db_conn, job_server)
