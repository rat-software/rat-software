"""
ScraperController

The ScraperController class controls the execution of the scraper check job.

Attributes:
    args (list): The args for the controller to stop it.
        args[0] (str): Name of browser process (chrome, chromium, firefox).

Methods:
    start(workingdir): Starts the scraper check job in a separate thread.

Example:
    scraper_controller = ScraperController()
    scraper_controller.start(workingdir)
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

        def check():
            call(["python", workingdir + "/jobs/job_scraper_check.py"])

        process1 = threading.Thread(target=check)
        process1.start()

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
