"""
Controller to start and manage the Sources Scraper.

This script is responsible for managing the lifecycle of the Sources Scraper, including stopping processes and resetting the database. It interacts with processes and web browsers to terminate them gracefully and performs necessary cleanup actions.

Dependencies:
    - threading
    - subprocess
    - psutil
    - time
    - os
    - sys
    - inspect
    - Custom libraries: lib_logger, lib_helper, lib_db
"""

# Import required libraries
import threading
from subprocess import call
import psutil
import time
import os
import sys
import inspect

# Import custom libraries
from libs.lib_logger import *
from libs.lib_helper import *
from libs.lib_db import *

class SourcesController:
    """
    A controller class for managing the Sources Scraper processes.

    Attributes:
        args (list): Arguments for the `stop` method.
        - args[0] (list): List of browser process names to be terminated.
        - db (object): Database object for interacting with the database.

    Methods:
        __init__(): Initializes the SourcesController object.
        __del__(): Destructor for the SourcesController object.
        stop(args: list): Stops specified processes and resets the database.
    """

    def __init__(self):
        """
        Initializes the SourcesController object.
        """
        # Initialization logic (if any) should be added here
        pass

    def __del__(self):
        """
        Destructor for the SourcesController object.

        Prints a message when the SourcesController object is destroyed.
        """
        print('Sources Controller object destroyed')

    def stop(self, args):

        """
        Stops the scraper processes and resets the database.

        This method identifies and terminates Python processes and specific browser instances.
        It also performs a cleanup operation to reset the database entries.

        Args:
            args (list): A list where:
                - args[0] (list): List of browser process names (e.g., "chrome", "chromium").
                - db (object): Database object for resetting the database.

        Raises:
            ValueError: If the database object is not provided in `args`.
        """

        # List of processes related to the scraper to be killed
        processes_to_kill = ["job_sources.py", "sources_scraper.py", "sources_reset.py", "job_reset_sources.py", "sources_controller_start.py"]
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

           
            # Wait for processes to terminate before resetting the database
        time.sleep(60)

        # Reset the database
        
        db.reset(job_server)

    

if __name__ == "__main__":
    """
    Main execution point for the SourcesController script.

    Creates a SourcesController instance, loads necessary configuration files,
    and calls the stop method to terminate processes and reset the database.
    """
    # Initialize the SourcesController
    sources_controller = SourcesController()

     # Determine the directory containing the job scripts
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Load configuration files
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")
    helper = Helper()
    db_cnf = helper.file_to_dict(path_db_cnf)
    path_sources_cnf = os.path.join(parentdir, "config", "config_sources.ini")

    # Initialize Helper and Database objects
    helper = Helper()
    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    db = DB(db_cnf, job_server, refresh_time)

    # Stop scraper processes and reset the database
    sources_controller.stop([["chromium", "chrome", "--headless=new", "uc_driver"], db, job_server])

    # Cleanup
    del helper
    del db
    del sources_controller
