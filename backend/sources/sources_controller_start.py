"""
Controller to start and manage the Sources Scraper.

This script manages the execution of the scraping processes by spawning
threads to run specified jobs. It identifies the correct working directory
and starts two processes:
- `source()`: Executes the scraping process.
- `reset()`: Resets any failed jobs.

The script determines the working directory based on the location of
the `job_sources.py` script.

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
import os
import sys
import inspect

# Import custom libraries
from libs.lib_logger import *
from libs.lib_helper import *
from libs.lib_db import *

class SourcesController:
    """
    A controller class for managing the Sources Scraper.

    Attributes:
        args (list): List of arguments for the `stop` method (not used in `start`).
        db (object): Database object (not used in `start` method).

    Methods:
        __init__(): Initializes the SourcesController object.
        __del__(): Destructor for the SourcesController object.
        start(workingdir): Starts the scraper by launching two jobs in separate threads.
    """

    def __init__(self):
        """
        Initializes the SourcesController object.
        """
        # Initialization logic here (if any)
        pass

    def __del__(self):
        """
        Destructor for the SourcesController object.

        Prints a message when the SourcesController object is destroyed.
        """
        print('Sources Controller object destroyed')

    def start(self, workingdir):
        """
        Starts the Sources Scraper by opening two jobs in separate threads:
        
        - `source()`: Calls `job_sources.py` to start the scraping process.
        - `reset()`: Calls `job_reset_sources.py` to reset failed jobs.

        Args:
            workingdir (str): The directory containing the job scripts.
        """

        def source():
            """
            Executes the job_sources.py script to start the scraping process.
            """
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_sources.py')
            os.system(job)   

        def reset():
            """
            Executes the job_reset_sources.py script to reset failed jobs.
            """
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_reset_sources.py')
            os.system(job)              

        # Start threads for the defined job functions
        process1 = threading.Thread(target=source)
        process1.start()

        process2 = threading.Thread(target=reset)
        process2.start()


if __name__ == "__main__":
    """
    Main execution point for the SourcesController script.

    Creates a SourcesController instance, determines the correct working
    directory for the job scripts, and starts the scraper.
    """
    sources_controller = SourcesController()

    # Determine the directory containing the job scripts
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(os.path.join(currentdir, 'jobs', 'job_sources.py')):
        workingdir = currentdir
    elif os.path.exists(os.path.join(parentdir, 'jobs', 'job_sources.py')):
        workingdir = parentdir
    else:
        raise FileNotFoundError("Job script 'job_sources.py' not found in expected directories.")

    # Start the SourcesController with the identified working directory
    sources_controller.start(workingdir)
    del sources_controller
