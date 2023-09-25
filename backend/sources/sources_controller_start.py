"""
Controller to start the Sources Scraper
"""

#load required libs
import threading
from subprocess import call
import psutil
import time
import os
import sys
import inspect

#load custom libs
from libs.lib_logger import *
from libs.lib_helper import *
from libs.lib_db import *

class SourcesController:

    """SourcesController"""
    args: list
    """The class has no args for the start function.
    \nThe args for the stop function are:
    \n<b>args[0]:list</b> = name of browser process (chrome, chromium, firefox)
    \n<b>db:object</b> = Database object
    """

    def __init__(self):
        self = self

    def __del__(self):
        """Destroy the sources controller"""
        print('Sources Controller object destroyed')

    def start(self, workingdir):
        """Method to start the controller by opening two jobs in threads:
        \n
        \n<b>source():</b> call `sources.jobs.job_sources` to start the scraping process.
        \n<b>reset():</b> call `sources.jobs.job_reset` script to reset failed jobs.
        """


        def source():
            call(["python", workingdir + "/jobs/job_sources.py"])

        def reset():
            call(["python", workingdir + "/jobs/job_reset_sources.py"])


        

        #Start threads for the definied job functions.
        process1 = threading.Thread(target=source)
        process1.start()

        process2 = threading.Thread(target=reset)
        process2.start()


if __name__ == "__main__":
    """Main call for the Sources Controller"""
    sources_controller = SourcesController()

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(currentdir + '/jobs/job_sources.py' ):
        workingdir = currentdir

    elif os.path.exists(parentdir + '/jobs/job_sources.py' ):
        workingdir = parentdir

    sources_controller.start(workingdir)
    del sources_controller
