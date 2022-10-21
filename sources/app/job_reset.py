#processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time

from lib_log import *

job_defaults = {
    'max_instances': 1
}

def job():
    os.system('python reset.py')

if __name__ == '__main__':

    write_to_log("Source\t reset\t \t ")
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')
    scheduler.add_job(job, 'interval', hours=1, next_run_time=datetime.now())
    scheduler.start()

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
