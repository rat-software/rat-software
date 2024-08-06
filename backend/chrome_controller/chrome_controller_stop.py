"""
Iterate over processes to find and terminate specific ones related to certain scripts.

This method checks each process to see if it is associated with particular scripts and terminates those processes if found.

Args:
    args (list): A list of script names to identify and terminate related processes.

Returns:
    None
"""

from subprocess import call
import psutil
import os
import inspect

class ChromeController:

    """
    Iterate over processes to find and terminate specific ones related to certain scripts.

    This method iterates over all processes to find and terminate those associated with specific script names provided in the args list.

    Args:
        args (list): A list of script names to identify and terminate related processes.

    Returns:
        None
    """

    def stop(self):
        

        # Iterate over all processes to find and kill specific ones based on conditions
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                # Check if the process is related to specific scripts and kill if found
                if "python" in proc.info['name'] and any(script in proc.info['cmdline'] for script in ["job_chrome.py", "chrome_reset.py", "chrome_controller_start.py"]):
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

if __name__ == "__main__":
    # Create an instance of ChromeController
    chrome_controller = ChromeController()

    # Get the current directory and its parent directory
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Determine the working directory based on the existence of a specific file
    workingdir = next(
        (
            directory
            for directory in [currentdir, parentdir]
            if os.path.exists(f'{directory}/jobs/job_chrome.py')
        ),
        None,
    )


    chrome_controller.stop()
