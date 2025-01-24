"""
ScraperReset

This class represents a controller for resetting sources in the scraper.

Attributes:
    db (object): Database object used to perform the reset operation.

Methods:
    __init__(db): Initializes the ScraperReset object with the provided database object.
    __del__(): Destructor for the ScraperReset object.
    reset(): Resets the sources in the scraper by calling the `reset` method on the database object.

Example:
    # Example usage of ScraperReset
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    db_cnf = os.path.join(currentdir, "../config/config_db.ini")

    helper = Helper()
    db_cnf = helper.file_to_dict(db_cnf)
    db = DB(db_cnf)

    scraper_reset = ScraperReset(db)
    scraper_reset.reset()
    del scraper_reset
"""

from libs.lib_helper import Helper
from libs.lib_db import DB
import os
import inspect

class ScraperReset:
    """
    Controller for resetting sources in the scraper.

    This class provides functionality to reset scraper-related sources by interacting with a database object.
    
    Attributes:
        db (DB): The database object used for resetting sources.
    """

    def __init__(self, db: DB):
        """
        Initializes the ScraperReset object with the given database object.

        Args:
            db (DB): The database object used for resetting sources.
        """
        self.db = db

    def __del__(self):
        """
        Destructor for the ScraperReset object.

        Prints a message to indicate that the ScraperReset object is being destroyed.
        """
        print('ScraperReset object destroyed')

    def reset(self, job_server):
        """
        Resets the sources in the scraper.

        Calls the `reset` method on the database object to perform the reset operation.
        """
        self.db.reset(job_server)

if __name__ == "__main__":
    """
    Entry point of the script when executed as the main program.

    - Determines the working directory for configuration files.
    - Loads database configuration and creates a database instance.
    - Initializes ScraperReset with the database object.
    - Performs the reset operation.
    - Cleans up by deleting instances of Helper, DB, and ScraperReset.
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Determine the configuration file path
    db_cnf = os.path.join(currentdir, "../config/config_db.ini")

    # Load database configuration
    helper = Helper()
    db_cnf = helper.file_to_dict(db_cnf)
    db = DB(db_cnf)

    # Load sources configuration
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
    sources_cnf = helper.file_to_dict(path_sources_cnf)
    job_server = sources_cnf['job_server']    

    # Initialize ScraperReset and perform reset
    scraper_reset = ScraperReset(db)
    scraper_reset.reset(job_server)

    # Clean up resources
    del db
    del scraper_reset
    del helper
