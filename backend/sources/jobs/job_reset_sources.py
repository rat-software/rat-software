"""
Reset Sources Job

This script defines a job function to reset failed scraping jobs. The scheduler is set to run the job once an hour.

Functions:
    job(): Calls the `sources.sources_reset` function to reset sources.
"""

#import required libs
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
    'max_instances': 1
}

def job():
    """
    Declare a job function to call `sources.sources_reset`
    """
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if "jobs" in currentdir:
        workingdir = parentdir
    else:
        workingdir = currentdir

    sources_job = 'python '+workingdir+'/sources_reset.py'

    os.system(sources_job)

if __name__ == '__main__':

    logger = Logger()
    logger.write_to_log("Source\t reset\t \t ")
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')
    scheduler.add_job(job, 'interval', hours=1, next_run_time=datetime.now())
    scheduler.start()

    del logger

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
