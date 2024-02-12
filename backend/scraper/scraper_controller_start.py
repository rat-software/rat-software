"""
ScraperController

This class represents a controller for managing the execution of scraper jobs.

Methods:
    __init__(): Initializes the ScraperController object.
    __del__(): Destructor for the ScraperController object.
    start(workingdir): Starts the scraper and reset jobs in separate threads.

Example:
    scraper_controller = ScraperController()
    scraper_controller.start(workingdir)
    del scraper_controller
"""


#processing libraries
import threading
from subprocess import call
import sys

import psutil

from libs.lib_helper import *
from libs.lib_db import *

import time

import os
import inspect

class ScraperController:

    def __init__(self):
        self = self

    def __del__(self):
        print('Scraper Controller object destroyed')

    def start(self, workingdir):

        def scraper():
            call(["python", workingdir + "/jobs/job_scraper.py"])

        def reset():
            call(["python", workingdir + "/jobs/job_reset_scraper.py"])
            

        process1 = threading.Thread(target=scraper)
        process1.start()

        process2 = threading.Thread(target=reset)
        process2.start()

if __name__ == "__main__":
    scraper_controller = ScraperController()

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(currentdir + '/jobs/job_scraper.py' ):
        workingdir = currentdir

    elif os.path.exists(parentdir + '/jobs/job_scraper.py' ):
        workingdir = parentdir

    scraper_controller.start(workingdir)
    del scraper_controller
