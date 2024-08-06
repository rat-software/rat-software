"""
Main script to start and manage different controllers and processes for a scraping application.

This script initializes and runs multiple controllers for different components of the application in separate threads. It uses the `threading` module to concurrently execute these controllers. 

Dependencies:
    - time: For timing-related operations.
    - os: For interacting with the operating system, including file path operations.
    - sys: For system-specific parameters and functions (though not used in this script).
    - inspect: For inspecting live objects.
    - threading: For running processes concurrently.
    - subprocess: For spawning new processes.
    - apscheduler.schedulers.background: For scheduling tasks (imported but not used in this script).
    - datetime: For working with dates and times (imported but not used in this script).
"""

import time
import os
import sys
import inspect
import threading
from subprocess import call

# Define the paths to the controllers
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

sources_controller = os.path.join(currentdir, "sources", "sources_controller_start.py")
scraper_controller = os.path.join(currentdir, "scraper", "scraper_controller_start.py")
classifier_controller = os.path.join(currentdir, "classifier", "classifier_controller_start.py")
chrome_controller = os.path.join(currentdir, "chrome_controller", "chrome_controller_start.py")

def source():
    """
    Function to start the Sources Controller process.

    Uses the subprocess.call() function to execute the sources_controller_start.py script.
    """
    os.system("python " + sources_controller)

    

def scraper():
    """
    Function to start the Scraper Controller process.

    Uses the subprocess.call() function to execute the scraper_controller_start.py script.
    """
    os.system("python " + scraper_controller)
    

def classifier():
    """
    Function to start the Classifier Controller process.

    Uses the subprocess.call() function to execute the classifier_controller_start.py script.
    """
    os.system("python " + classifier_controller)

def chrome():
    """
    Function to start the Chrome Controller process.

    Uses the subprocess.call() function to execute the chrome_controller_start.py script.
    """
    os.system("python " + classifier_controller)

if __name__ == "__main__":
    """
    Main entry point of the script.

    Starts each controller in a separate thread for concurrent execution. The script initializes
    and starts threads for source, scraper, classifier, and chrome controllers.
    """
    # Start threads for each defined job function
    process1 = threading.Thread(target=source, name="SourceControllerThread")
    process1.start()

    process2 = threading.Thread(target=scraper, name="ScraperControllerThread")
    process2.start()

    process3 = threading.Thread(target=classifier, name="ClassifierControllerThread")
    process3.start()

    process4 = threading.Thread(target=chrome, name="ChromeControllerThread")
    process4.start()

    # Optional: Join threads to ensure main thread waits for their completion
    process1.join()
    process2.join()
    process3.join()
    process4.join()
