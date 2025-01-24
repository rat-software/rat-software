"""
ScraperController

This class represents a controller for managing the stopping of scraper processes and related jobs.

Methods:
    __init__(): Initializes the ScraperController object.
    __del__(): Destructor for the ScraperController object.
    stop(args): Stops the running scraper and related processes.

Args:
    args (list): The arguments for stopping the processes.
        args[0] (list): List of browser names to stop (e.g., ["chrome", "chromium"]).
        args[1] (object): Database object (used for resetting database states).

Example:
    scraper_controller = ScraperController()
    scraper_controller.stop([["chrome", "chromium"], db])
    del scraper_controller
"""

import threading
from subprocess import call
import sys
import psutil
from libs.lib_helper import Helper
from libs.lib_db import DB
import time
import os
import inspect

class ScraperController:
    """
    Manages the stopping of scraper processes and related jobs.

    This class provides functionality to terminate running processes related to scraping, including specific Python scripts
    and browser processes, by using the `psutil` library.

    Attributes:
        None
    """

    def __init__(self):
        """
        Initializes the ScraperController instance.
        
        The constructor does not need to perform any specific initialization in this implementation.
        """
        # No specific initialization required for this class
        pass

    def __del__(self):
        """
        Destructor for the ScraperController instance.
        
        This method is called when the object is about to be destroyed.
        It prints a message to indicate that the ScraperController object is being cleaned up.
        """
        print('ScraperController object destroyed')

    def stop(self, args:list):
        """
        Stops the running scraper and related processes.

        This method iterates over the current running processes and terminates those associated with scraping jobs
        or specified browsers. It identifies processes based on their names or command line arguments and attempts to kill them.

        Args:
            args (list): Contains information for stopping processes.
                args[0] (list): List of browser names to stop (e.g., ["chrome", "chromium"]).
                args[1] (object): A database object used for resetting database states (not utilized in this method).
        """

        # List of processes related to the scraper to be killed
        processes_to_kill = ["job_scraper.py", "scraper_start.py", "scraper_reset.py", "job_reset_scraper.py", "scraper_controller_start.py"]
        kill_browser = False

        # Iterate over all running processes
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                if "python" in proc.info['name']:
                    # Check if the process name or command line matches any in the kill list
                    if proc.info['cmdline']:
                        if any(name in proc.info['name'] or name in proc.info['cmdline'] for name in processes_to_kill):
                            proc.kill()  # Kill the process
                            kill_browser = True

                # Kill browser processes specified in the arguments
                if kill_browser:
                    for browser in args[0]:
                        if browser in proc.info['name'] or browser in proc.info['cmdline']:
                            proc.kill()

            except Exception as e:
                pass
            
        # Wait for 60 seconds before resetting the database
        time.sleep(60)
        db.reset(job_server)  # Call the reset method on the database object

if __name__ == "__main__":
    """
    Entry point of the script when executed as the main program.

    - Initializes the ScraperController.
    - Determines the working directory where the job scripts are located.
    - Loads database configuration and creates a DB instance.
    - Stops scraper and browser processes.
    - Cleans up by deleting instances of Helper, DB, and ScraperController.
    """
    scraper_controller = ScraperController()

    # Determine the directory containing the job scripts
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Load configuration files
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")
    helper = Helper()
    db_cnf = helper.file_to_dict(path_db_cnf)
    db = DB(db_cnf)

    # Load sources configuration
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
    sources_cnf = helper.file_to_dict(path_sources_cnf)
    job_server = sources_cnf['job_server']

    # Stop the scraper and browser processes
    scraper_controller.stop([["chromium", "chrome", "--headless=new", "uc_driver"], db, job_server])

    # Clean up resources
    del helper
    del db
    del scraper_controller
