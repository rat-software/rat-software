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
        
        # NEU: Konsolen-Feedback zu blockierten Jobs unter 10 Minuten
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
                print(f"INFO: {waiting} Job(s) stecken in Progress 2/-1 fest, sind aber noch keine 10 Min. alt. Sie werden beim nächsten Aufruf ignoriert!")
        except Exception as e:
            pass
            
        sources_pending = db.get_sources_pending(job_server)  # Retrieve all pending sources
        print(f"Gefundene Jobs, die fuer den Reset qualifiziert sind (> 10 Min alt): {len(sources_pending)}")      

        for s in sources_pending:
            # 1. Sicherstellen, dass wir keine IndexErrors werfen
            raw_composite_id = s[0]  # Das ist z.B. 'result_ai_source:292'
            source_id = s[1] if len(s) > 1 else None
            
            # 2. Die Composite-ID mithilfe der DB-Helper-Methode aufsplitten
            fk_column, result_id = db._parse_id(raw_composite_id)
            
            # Da das Skript alt ist und "result_source_id" an manchen Stellen braucht, 
            # nutzen wir hier die bereinigte 'result_id' als Fallback
            result_source_id = result_id 

            if source_id:
                print(f"Resetting source ID: {source_id} (Composite: {raw_composite_id})")
                log = f"Reset \t source \t {source_id} \t"
                self.logger.write_to_log(log)
                
                # WICHTIG: raw_composite_id übergeben, damit die DB weiß, ob es 'result' oder 'result_ai_source' ist!
                counter = db.get_source_counter_result(raw_composite_id) + 1
                progress = 0
                created_at = datetime.now()
                
                db.reset_result_source(progress, counter, created_at, source_id)
                db.delete_source_pending(source_id, progress, created_at)

            else:
                print(f"Resetting missing source for entity: {raw_composite_id}")
                log = f"Reset \t source_failed_missing_id \t {raw_composite_id} \t"
                self.logger.write_to_log(log)
                
                # WICHTIG: Statt den Eintrag zu löschen (was zur Endlosschleife führt),
                # setzen wir ihn zurück und erhöhen den Counter.
                counter = db.get_source_counter_result(raw_composite_id) + 1
                progress = 0
                created_at = datetime.now()
                
                # Aktualisiert den Eintrag in der korrekten Tabelle (result_source oder result_ai_source)
                db.update_result_source_result(raw_composite_id, progress, counter, created_at)

        db.update_sources_failed(job_server) # Reset all finally failed sources (counter >= 3)

            

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