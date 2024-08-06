#processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
from datetime import datetime

import os
import inspect


job_defaults = {
    'max_instances': 2
}

def job():
    """
    Job function for running the scraper.

    Returns:
        None
    """    
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if "jobs" in currentdir:
        workingdir = parentdir
    else:
        workingdir = currentdir

    scraper_job = 'python '+workingdir+'/scraper_start.py'

    os.system(scraper_job)

if __name__ == '__main__':
    """
    Entry point for running the scraper job.

    Returns:
        None
    """
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')
    scheduler.add_job(job, 'interval', seconds=20, next_run_time=datetime.now())
    scheduler.start()

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
