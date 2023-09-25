
import time
import os
import sys
import inspect

#processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
from datetime import datetime

import time

import os

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

sources_controller = currentdir + "/sources/sources_controller_start.py"
scraper_controller = currentdir + "/scraper/scraper_controller_start.py"
classifier_controller = currentdir + "/classifier/classifier_controller_start.py"

def source():
    call(["python", sources_controller])

def scraper():
    call(["python", scraper_controller])

def classifier():
    call(["python", classifier_controller])

if __name__ == "__main__":
    #Start threads for the definied job functions.
    process1 = threading.Thread(target=source)
    process1.start()

    process2 = threading.Thread(target=scraper)
    process2.start()

    process3 = threading.Thread(target=classifier)
    process3.start()
