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
    'max_instances': 1
}

def job():

    """
    Execute the classifier job.

    Returns:
        None
    """

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if "jobs" in currentdir:
        workingdir = parentdir
    else:
        workingdir = currentdir

    classifier_job = 'python '+workingdir+'/classifier_reset.py'

    os.system(classifier_job)

if __name__ == '__main__':

    """
    Entry point for the job classifier script.

    Returns:
        None
    """    

    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')
    scheduler.add_job(job, 'interval', hours=1, next_run_time=datetime.now())
    scheduler.start()

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
