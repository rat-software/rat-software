"""
ScraperController

This class represents a controller for managing the execution of scraper jobs and reset tasks.

Methods:
    __init__(): Initializes the ScraperController object.
    __del__(): Destructor for the ScraperController object, cleans up resources.
    start(workingdir): Starts the scraper and reset jobs in separate threads.

Example:
    scraper_controller = ScraperController()
    scraper_controller.start(workingdir)
    del scraper_controller
"""

# Import necessary libraries
import threading
from subprocess import call
import os
import inspect

class ScraperController:
    """
    Controls the execution of scraper and reset jobs.

    This class manages the launching of two separate Python scripts: one for scraping data and one for resetting scraper states.
    It runs each script in its own thread to allow concurrent execution.

    Attributes:
        None
    """

    def __init__(self):
        """
        Initializes the ScraperController instance.
        
        The constructor does not need to perform any specific initialization for this example.
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

    def start(self, workingdir):
        """
        Starts the scraper and reset jobs in separate threads.

        Args:
            workingdir (str): The directory where the job scripts are located.

        This method creates and starts two threads:
        - One to execute the scraper script.
        - One to execute the reset scraper script.
        """
        def scraper():
            """
            Executes the scraper job script.
            """
            # Call the scraper script using subprocess
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_scraper.py')
            os.system(job)            
            

        def reset():
            """
            Executes the reset scraper job script.
            """
            # Call the reset scraper script using subprocess
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_reset_scraper.py')
            os.system(job)   
        
        # Create and start the thread for the scraper job
        scraper_thread = threading.Thread(target=scraper)
        scraper_thread.start()

        # Create and start the thread for the reset job
        reset_thread = threading.Thread(target=reset)
        reset_thread.start()

if __name__ == "__main__":
    """
    Entry point of the script when executed as the main program.

    - Initializes the ScraperController.
    - Determines the correct working directory for job scripts.
    - Starts the scraper and reset jobs.
    - Cleans up by deleting the ScraperController instance.
    """
    scraper_controller = ScraperController()

    # Determine the working directory where the job scripts are located
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(os.path.join(currentdir, 'jobs', 'job_scraper.py')):
        workingdir = currentdir
    elif os.path.exists(os.path.join(parentdir, 'jobs', 'job_scraper.py')):
        workingdir = parentdir
    else:
        raise FileNotFoundError("job_scraper.py script not found in expected directories.")

    # Start the scraper and reset jobs
    scraper_controller.start(workingdir)

    # Explicitly delete the ScraperController instance
    del scraper_controller
