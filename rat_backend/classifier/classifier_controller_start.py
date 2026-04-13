"""
ClassifierController

This class represents a controller for starting the classifier and resetting jobs.

Methods:
    start(workingdir): Starts the classifier and resets jobs.

Args:
    workingdir (str): The working directory.

Returns:
    None

Example:
    classifier_controller = ClassifierController()
    classifier_controller.start(workingdir)
"""

# Import necessary libraries
import threading
from subprocess import call
import os
import inspect


class ClassifierController:
    """
    A class used to control the starting of the classifier and resetting jobs.

    Methods:
        start: Starts the classifier and resets jobs.
    """

    def start(self, workingdir):
        """
        Start the classifier and reset jobs.

        Args:
            workingdir (str): The working directory.

        Returns:
            None
        """
        def classifier():
            """
            Function to start the classifier job.
            This function calls the job_classifier.py script using the subprocess call.
            """
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_classifier.py')
            os.system(job)

        def reset():
            """
            Function to start the job reset classifier.
            This function calls the job_reset_classifier.py script using the subprocess call.
            """
            job = 'python ' + os.path.join(workingdir, "jobs", 'job_reset_classifier.py')
            os.system(job)

        # Create a new thread for the classifier function and start it
        process1 = threading.Thread(target=classifier)
        process1.start()

        # Create a new thread for the reset function and start it
        process2 = threading.Thread(target=reset)
        process2.start()


if __name__ == "__main__":
    # Initialize the ClassifierController object
    classifier_controller = ClassifierController()

    # Get the current directory of the script
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    # Get the parent directory of the current directory
    parentdir = os.path.dirname(currentdir)

    # Determine the working directory based on the presence of job_classifier.py
    workingdir = currentdir if os.path.exists(os.path.join(currentdir, 'jobs', 'job_classifier.py')) else parentdir

    # Start the classifier and reset jobs
    classifier_controller.start(workingdir)
