"""
Reset Query Sampler Job

This script defines a background job to periodically reset failed QS jobs.
The scheduler is set to run the reset check at defined intervals.
"""

# Import processing and scheduling libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
from datetime import datetime
import inspect

# Job defaults configuration
job_defaults = {
    'max_instances': 1
}

def job():
    """
    Execute the QS Reset script.

    This function determines the correct working directory and then runs
    the qs_reset.py script using the system's command line interface.
    """
    # Determine the directory where this script is located
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    # Set the working directory based on the current directory
    if "jobs" in currentdir:
        workingdir = parentdir
    else:
        workingdir = currentdir

    # Construct the command to run the reset script
    qs_reset_job = 'python ' + os.path.join(workingdir, 'query_sampler_reset.py')

    # Execute the reset script
    os.system(qs_reset_job)

if __name__ == '__main__':
    """
    Entry point for the job reset QS script.
    """
    print("QS Reset Scheduler started. Waiting for next execution...")
    
    # Create a BackgroundScheduler instance
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='Europe/Berlin')

    # Add a job to the scheduler that runs the `job` function every 30 minutes
    # It also runs immediately upon startup (next_run_time=datetime.now())
    scheduler.add_job(job, 'interval', minutes=30, next_run_time=datetime.now())

    # Start the scheduler
    scheduler.start()

    try:
        # Keep the script running and wait for interrupts
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Shutdown the scheduler gracefully on interrupt
        scheduler.shutdown()