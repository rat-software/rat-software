import time
from classifier_db_lib import *

import psutil
for proc in psutil.process_iter(attrs=['pid', 'name']):

    if 'python' in proc.info['name']:

        try:
            if "classifier_start.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "job_classifier.py" in proc.cmdline():
                proc.kill()
        except:
            pass


        try:
            if "classifier.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "firefox" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "geckodriver" in proc.cmdline():
                proc.kill()
        except:
            pass

time.sleep(30)

for proc in psutil.process_iter(attrs=['pid', 'name']):
    if 'python' in proc.info['name']:

        try:
            if "classifier_start.py" in proc.cmdline():
                proc.kill()
        except:
            pass


        try:
            if "job_classifier.py" in proc.cmdline():
                proc.kill()
        except:
            pass


        try:
            if "classifier.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "firefox" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "geckodriver" in proc.cmdline():
                proc.kill()
        except:
            pass


time.sleep(60)

reset()
