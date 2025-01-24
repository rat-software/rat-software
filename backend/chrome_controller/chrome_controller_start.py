"""
Starts a Chrome controller by running a job in a new thread.

The code initializes a Chrome controller by starting a new thread to run a specified job, which involves calling a Python script in a separate process.

Args:
    workingdir (str): The working directory where the job is located.

Returns:
    None
"""

import threading
from subprocess import call
import os
import inspect

class ChromeController:

    """
    Start a new thread to run a specified job.

    This method initiates a new thread to execute a specific job provided with the working directory.

    Args:
        workingdir (str): The working directory where the job is located.

    Returns:
        None
    """    

    def start(self, workingdir):

        def chrome():
            """
            Function to start the job reset classifier.
            This function calls the job_reset_classifier.py script using the subprocess call.
            """
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_chrome.py')
            os.system(job)

        # Create a new thread for the classifier function and start it
        process1 = threading.Thread(target=chrome)
        process1.start()        


if __name__ == "__main__":
    # Create an instance of ChromeController
    chrome_controller = ChromeController()

    # Get the current directory and its parent directory
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Determine the working directory based on the existence of a specific file
    workingdir = currentdir if os.path.exists(f"{currentdir}/jobs/job_chrome.py") else parentdir

    # Start the controller with the determined working directory
    chrome_controller.start(workingdir)
