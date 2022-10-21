#processing libraries
import threading
from subprocess import call
from apscheduler.schedulers.background import BackgroundScheduler

def classifier():
    call(["python", "job_classifier.py"])


process1 = threading.Thread(target=classifier)
process1.start()


#todo: job and function to download I don't care about cookies
