# Processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
from datetime import datetime
import inspect

# Job defaults configuration
job_defaults = {
    'max_instances': 1  # Limits the number of concurrent instances of this job to 1
}

def job():
    """
    Execute the classifier reset job.

    This function determines the working directory based on the location of the script and
    then executes the `classifier_reset.py` script using the system's command line interface.

    Returns:
        None
    """
    # Determine the directory where this script is located
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Set the working directory based on whether "jobs" is in the path
    if "jobs" in currentdir:
        workingdir = parentdir
    else:
        workingdir = currentdir

    # Construct the command to run the classifier reset script
    classifier_job = 'python ' + os.path.join(workingdir, 'classifier_reset.py')

    # Execute the classifier reset script
    os.system(classifier_job)

if __name__ == '__main__':
    """
    Entry point for the classifier reset script.

    This script sets up a background scheduler to run the `job` function at regular intervals.
    It keeps the script running and handles interruptions to shut down the scheduler gracefully.

    Returns:
        None
    """
    # Create a BackgroundScheduler instance with job defaults
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')

    # Add a job to the scheduler that runs the `job` function every hour
    scheduler.add_job(job, 'interval', hours=1, next_run_time=datetime.now())

    # Start the scheduler
    scheduler.start()

    try:
        # Keep the script running and wait for interrupts
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Shutdown the scheduler gracefully on interrupt
        scheduler.shutdown()
