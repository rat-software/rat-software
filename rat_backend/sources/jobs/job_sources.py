"""
Start Sources Scraper Job

This script defines a job function to start the sources scraper. The maximum number of job instances is set to 2 by default, but can be changed based on server capacity. The job is executed every 10 seconds by default, but can also be adjusted according to server capacity.

Functions:
    job(): Calls the `sources.sources_scraper` function to start the sources scraper.
"""

#import required libs
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import time

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

#import custom libs
from libs.lib_logger import *

job_defaults = {
    'max_instances': 2
}

def job():
    """
    Declare a job function to call `sources.sources_scraper`
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if "jobs" in currentdir:
        workingdir = parentdir
    else:
        workingdir = currentdir

    sources_job = 'python '+workingdir+'/sources_scraper.py'
    os.system(sources_job)

if __name__ == '__main__':

    logger = Logger()
    logger.write_to_log("Source\t scraper\t started\t ")
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')
    scheduler.add_job(job, 'interval', seconds=60, next_run_time=datetime.now())
    scheduler.start()

    del logger

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()