# keyword_controller_start.py

import threading
import os
import inspect

class KeywordController:
    """
    A class for controlling the startup of the keyword generator.

    Methods:
        start: Starts the job scheduler for keyword generation.
    """

    def start(self, workingdir: str):
        """
        Starts the scheduler for keyword generation.

        Args:
            workingdir (str): The working directory where the 'jobs' directory is located.

        Returns:
            None
        """
        def start_job():
            """
            Internal function to start the scheduler job.
            This function calls the job_qs.py script.
            """
            # Ensures that the path to the job script is correct
            job_path = os.path.join(workingdir, "jobs", 'job_qs.py')
            print(f"Starte Job: python {job_path}")
            os.system(f'python {job_path}')

        # Creates a new thread for the start_job function and starts it
        process = threading.Thread(target=start_job)
        process.start()
        print("Keyword Generation Controller launched.")


if __name__ == "__main__":
    # Initializes the KeywordController object
    keyword_controller = KeywordController()

    # Determines the current directory of the script
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    # Ermittelt das übergeordnete Verzeichnis
    parentdir = os.path.dirname(currentdir)

    # Sets the working directory. It is assumed that the script is located in the root directory
    # or a subdirectory, and that the 'jobs' directory is in the root directory.
    workingdir = parentdir if "controller" in currentdir else currentdir

    # Start the controller
    keyword_controller.start(workingdir)