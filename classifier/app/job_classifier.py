#processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
from datetime import datetime

job_defaults = {
    'max_instances': 3
}

def job():
    os.system('python classifier.py')

if __name__ == '__main__':


    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')
    scheduler.add_job(job, 'interval', seconds=20, next_run_time=datetime.now())
    scheduler.start()

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
