#processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler

def source():
    call(["python", "job_sources.py"])

def reset():
    call(["python", "job_reset.py"])

process1 = threading.Thread(target=source)
process1.start()

process2 = threading.Thread(target=reset)
process2.start()

#todo: job and function to download I don't care about cookies
