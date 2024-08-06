
"""
Execute a job using subprocess.

This function determines the working directory based on the presence of 'jobs', constructs a path for a classifier job, and executes the job using subprocess.

Args:
    None

Returns:
    None
"""

from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
from datetime import datetime
import inspect

job_defaults = {
    'max_instances': 1
}

def job():

    """
    Execute a job using subprocess.

    This function determines the working directory based on the presence of 'jobs', constructs a path for a classifier job, and executes the job using subprocess.

    Args:
        None

    Returns:
        None
    """
    
    # Get the current directory and parent directory
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Determine the working directory based on the presence of 'jobs' in the current directory
    workingdir = parentdir if "jobs" in currentdir else currentdir

    # Construct the command to run the classifier script
    chrome_job = 'python ' + os.path.join(workingdir, 'chrome_reset.py')

    # Execute the classifier script
    os.system(chrome_job)


if __name__ == '__main__':
    # Initialize the scheduler with job defaults and timezone
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')

    # Add the job to the scheduler to run at intervals
    scheduler.add_job(job, 'interval', hours=1, next_run_time=datetime.now())

    # Start the scheduler
    scheduler.start()

    try:
        # Keep the program running by
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
