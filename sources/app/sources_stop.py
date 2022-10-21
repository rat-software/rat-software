

import time

from lib_db import *
from lib_log import *


write_to_log("Stop\t the\t source scraper")

import json

def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

sources_cnf = file_to_dict("config_sources.ini")

job_server = sources_cnf['job_server']


import psutil
for proc in psutil.process_iter(attrs=['pid', 'name']):



    if 'python' in proc.info['name']:

        try:
            if "job_sources.py" in proc.cmdline():
                proc.kill()
        except:
            pass


        try:
            if "sources.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "reset.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "job_reset.py" in proc.cmdline():
                proc.kill()
        except:
            pass


    try:
        if "firefox" in proc.info['name']:
            proc.kill()
    except:
        pass

    try:
        if "geckodriver" in proc.info['name']:
            print("gecko")
            proc.kill()
    except:
        pass

time.sleep(30)

for proc in psutil.process_iter(attrs=['pid', 'name']):
    if 'python' in proc.info['name']:


        try:
            if "job_sources.py" in proc.cmdline():
                proc.kill()
        except:
            pass


        try:
            if "sources.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "reset.py" in proc.cmdline():
                proc.kill()
        except:
            pass

        try:
            if "job_reset.py" in proc.cmdline():
                proc.kill()
        except:
            pass



    try:
        if "firefox" in proc.info['name']:
            proc.kill()
    except:
        pass

    try:
        if "geckodriver" in proc.info['name']:
            print("gecko")
            proc.kill()
    except:
        pass



time.sleep(60)

reset(job_server)
