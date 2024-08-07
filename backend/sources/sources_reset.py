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

        This method retrieves all pending sources from the database, checks if they have been pending for more than a specified threshold (0.2 hours), and if so, resets their status.

        Args:
            db (object): Database object used to interact with the sources and update their status.
        """
        sources_pending = db.get_sources_pending(job_server)  # Retrieve all pending sources       

        for s in sources_pending:
            result_source_id = s[0]
            source_id = s[1]
            result_id = s[2]
            
            if source_id:
   
                print(f"Resetting source ID: {source_id}")
                log = f"Reset \t source \t {source_id} \t"
                self.logger.write_to_log(log)
                
                # Update the source's status in the database
                counter = db.get_source_counter_result(result_id) + 1
                progress = 0
                created_at = datetime.now()
                
                db.reset_result_source(progress, counter, created_at, source_id)
                db.delete_source_pending(source_id, progress, created_at)

            else:
                print(f"Resetting source ID: {source_id}")
                log = f"Reset \t source \t {source_id} \t"
                self.logger.write_to_log(log)
                db.delete_result_source_pending(result_source_id)

        db.update_sources_failed(job_server) # Reset all finally failed sources (counter > 10)

            



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
