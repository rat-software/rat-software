"""
Class to handle the resetting of failed scraping jobs.

This class provides functionality to reset scraping jobs that have failed or been pending for too long. It updates the status of these jobs and logs the operations for tracking purposes.

Dependencies:
    - datetime: For timestamp operations.
    - json: For handling JSON data (if required in other parts of the code).
    - os: For path operations.
    - inspect: For inspecting the current file path.
    - Custom libraries: lib_db, lib_logger, lib_helper
"""

# Import custom libraries
from libs.lib_db import *
from libs.lib_logger import *
from libs.lib_helper import *

# Import required libraries
from datetime import datetime
import os
import inspect

class SourcesReset:
    """
    Handles the resetting of failed scraping jobs.

    Attributes:
        db (object): Database object used for querying and updating job statuses.
        logger (object): Logger object used for logging reset operations.

    Methods:
        __init__(db: object, logger: object): Initializes the SourcesReset object.
        __del__(): Destructor for the SourcesReset object.
        reset(db: object): Resets jobs that have been pending for too long.
    """

    def __init__(self, db: object, logger: object):
        """
        Initializes the SourcesReset object.

        Args:
            db (object): Database object for querying and updating job statuses.
            logger (object): Logger object for logging operations.
        """
        self.db = db
        self.logger = logger

    def __del__(self):
        """
        Destructor for the SourcesReset object.

        Prints a message when the SourcesReset object is destroyed.
        """
        print('Sources Reset object destroyed')

    def reset(self, db: object, job_server):
        """
        Resets the jobs that have been pending for too long.

        This method retrieves all pending sources from the database, checks if they have been pending for more than a specified threshold (e.g., 10 minutes), and if so, resets their status.
        Finally, it also expires any stuck jobs older than 14 days to prevent them from clogging up the system.

        Args:
            db (object): Database object used to interact with the sources and update their status.
            job_server (str): Name of the job server running the scraper.
        """
        
        # NEW: Console feedback for blocked jobs under 10 minutes
        try:
            conn = db.connect_to_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT SUM(cnt) FROM (
                    SELECT count(*) as cnt FROM result_image WHERE (progress=2 OR progress=-1) AND created_at >= now() - interval '10 minutes'
                    UNION ALL SELECT count(*) as cnt FROM result_source WHERE (progress=2 OR progress=-1) AND created_at >= now() - interval '10 minutes'
                    UNION ALL SELECT count(*) as cnt FROM result_ai_source WHERE (progress=2 OR progress=-1) AND created_at >= now() - interval '10 minutes'
                ) AS t
            """)
            waiting = cur.fetchone()[0]
            conn.close()
            if waiting and waiting > 0:
                print(f"INFO: {waiting} job(s) are stuck in Progress 2/-1 but are not yet 10 minutes old. They will be ignored in this run!")
        except Exception as e:
            pass
            
        sources_pending = db.get_sources_pending(job_server)  # Retrieve all pending sources
        print(f"Found jobs qualifying for reset (> 10 min old): {len(sources_pending)}")      

        for s in sources_pending:
            # 1. Ensure that we don't throw any IndexErrors
            raw_composite_id = s[0]  # This is e.g., 'result_ai_source:292'
            source_id = s[1] if len(s) > 1 else None
            
            # 2. Split the composite ID using the DB helper method
            fk_column, result_id = db._parse_id(raw_composite_id)
            
            # Since the script is old and requires "result_source_id" in some places, 
            # we use the cleaned 'result_id' as a fallback here
            result_source_id = result_id 

            if source_id:
                print(f"Resetting source ID: {source_id} (Composite: {raw_composite_id})")
                log = f"Reset \t source \t {source_id} \t"
                self.logger.write_to_log(log)
                
                # IMPORTANT: Pass raw_composite_id so the DB knows whether it is 'result', 'result_ai_source' or 'result_image'!
                counter = db.get_source_counter_result(raw_composite_id) + 1
                progress = 0
                created_at = datetime.now()
                
                db.reset_result_source(progress, counter, created_at, source_id)
                db.delete_source_pending(source_id, progress, created_at)

            else:
                print(f"Resetting missing source for entity: {raw_composite_id}")
                log = f"Reset \t source_failed_missing_id \t {raw_composite_id} \t"
                self.logger.write_to_log(log)
                
                # IMPORTANT: Instead of deleting the entry (which leads to an infinite loop),
                # we reset it and increase the counter.
                counter = db.get_source_counter_result(raw_composite_id) + 1
                progress = 0
                created_at = datetime.now()
                
                # Updates the entry in the correct table
                db.update_result_source_result(raw_composite_id, progress, counter, created_at)

        # Reset all finally failed sources (counter >= 3)
        db.update_sources_failed(job_server) 

        # --- NEW CODE: Expire old sources stuck beyond 14 days ---
        try:
            print("Expiring old stuck sources older than 14 days...")
            db.expire_old_pending_sources()
        except Exception as e:
            self.logger.write_to_log(f"Error expiring old sources: {str(e)}")
            print(f"Error expiring old sources: {str(e)}")
            

if __name__ == "__main__":
    """
    Main execution point for the SourcesReset script.

    Initializes the logger, database, and SourcesReset objects, and performs the reset operation for failed scraping jobs.
    """
    # Initialize the logger
    logger = Logger()
    logger.write_to_log("Reset \t \t sources \t ")

    # Determine the directory containing the configuration files
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    path_db_cnf = os.path.join(currentdir, "../config/config_db.ini")
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")

    # Initialize Helper and Database objects
    helper = Helper()
    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    db = DB(db_cnf, job_server, refresh_time)

    # Initialize the SourcesReset object and perform the reset operation
    sources_reset = SourcesReset(db, logger)
    sources_reset.reset(db, job_server)

    # Cleanup
    del logger
    del db
    del sources_reset