"""
ScraperController

This class represents a controller for managing the stopping of scraper jobs.

Methods:
    __init__(): Initializes the ScraperController object.
    __del__(): Destructor for the ScraperController object.
    stop(args): Stops the running scraper and scraper check processes.

Args:
    args (list): The arguments for stopping the processes.
        args[0] (list): List of process names to stop.
        args[1] (object): Database object.

Example:
    scraper_controller = ScraperController()
    scraper_controller.stop([["chrome", "chromium"], db])
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

    def stop(self, args:list):

        for proc in psutil.process_iter(attrs=['pid', 'name']):

            if ("python" in proc.info['name']):

                print(proc)
                
                try:
                    if ("scraper_check.py" in proc.info['name']) or ("scraper_check.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("job_scraper_check.py" in proc.info['name']) or ("job_scraper_check.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass


        time.sleep(60)

if __name__ == "__main__":
    scraper_controller = ScraperController()

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(currentdir + '/jobs/job_scraper.py' ):
        workingdir = currentdir

    elif os.path.exists(parentdir + '/jobs/job_scraper.py' ):
        workingdir = parentdir

    path_db_cnf = workingdir+"/config/config_db.ini"
    helper = Helper()

    db_cnf = helper.file_to_dict(path_db_cnf)

    db = DB(db_cnf)

    scraper_controller.stop([["chrome", "chromium"], db])

    del helper
    del db
    del scraper_controller
