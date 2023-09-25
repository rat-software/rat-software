"""
Function to start the sources_scraper.
\nThe default value for the maximum number of job instances is 3, but it can be changed depending on the server capacity.
\nThe job is executed every 60 seconds by default, but it can also be changed according to the server's capacities.
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
    scheduler.add_job(job, 'interval', seconds=10, next_run_time=datetime.now())
    scheduler.start()

    del logger

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
