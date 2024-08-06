"""
Controller class for stopping the classifier.

Methods:
    stop: Stop the classifier and associated processes.

Attributes:
    args (list): The args for the controller to stop it.

Args:
    args[0] (list): List of browser processes to stop.
    db (object): Database object.

"""   

from subprocess import call
import psutil
from libs.lib_helper import Helper
from libs.lib_db import DB
import time
import os
import inspect

class ClassifierController:
    """
    A class used to control and stop the classifier and associated processes.

    Methods:
        stop: Stop the classifier and associated processes.
    """

    def stop(self, args:list):
        """
        Stop the classifier and associated processes.

        Args:
            args[0] (list): List of browser processes to stop.
            db (object): Database object.

        Returns:
            None
        """
        # List of processes related to the classifier to be killed
        processes_to_kill = [
            "job_classifier.py", "classifier.py",
            "classifier_reset.py", "job_reset_classifier.py", "classifier_controller_start.py"
        ]

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
    # Initialize the ClassifierController object
    classifier_controller = ClassifierController()

    # Determine the directory containing the job scripts
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Load configuration files
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")
    helper = Helper()
    db_cnf = helper.file_to_dict(path_db_cnf)
    db = DB(db_cnf)

    # Initialize the Helper object
    helper = Helper()

    # Convert the configuration file to a dictionary
    db_cnf = helper.file_to_dict(path_db_cnf)

    # Initialize the DB object with the configuration dictionary
    db = DB(db_cnf)

    # Load sources configuration
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
    sources_cnf = helper.file_to_dict(path_sources_cnf)
    job_server = sources_cnf['job_server']    

    # Call the stop method to stop the classifier and browser processes
    classifier_controller.stop([["chromium", "chrome", "--headless=new", "uc_driver"], db, job_server])
