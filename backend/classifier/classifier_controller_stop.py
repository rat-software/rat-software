"""
Controller class for stopping the classifier.

Methods:
    __init__: Initialize the ClassifierController object.
    __del__: Destructor for the ClassifierController object.
    stop: Stop the classifier and associated processes.

Attributes:
    args (list): The args for the controller to stop it.

Args:
    args[0] (list): List of browser processes to stop.
    db (object): Database object.

"""   

#processing libraries
import threading
from subprocess import call
import sys

import psutil

from libs.lib_helper import *
from libs.lib_db import *

import time

import os
import inspect

class ClassifierController:

    def __init__(self):
        """
        Initialize the ClassifierController object.
        """        
        self = self

    def __del__(self):
        """
        Destructor for the ClassifierController object.
        """        
        print('Classifier Controller object destroyed')


    def stop(self, args:list):
        """
        Stop the classifier and associated processes.

        Args:
            args[0] (list): List of browser processes to stop.
            db (object): Database object.

        Returns:
            None
        """

        for proc in psutil.process_iter(attrs=['pid', 'name']):

            if ("python" in proc.info['name']):

                try:
                    if ("python.exe" in proc.info['name']):

                        proc.kill()
                except:
                    pass

                try:
                    if ("job_classifier.py" in proc.info['name']) or ("job_classifier.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("classifier.py" in proc.info['name']) or ("classifier.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("classifier_reset.py" in proc.info['name']) or ("classifier_reset.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("job_reset_classifier.py" in proc.info['name']) or ("job_reset_classifier.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

            try:
                for browser in args[0]:

                    if (browser in proc.info['name']) or (browser in proc.cmdline()):

                        proc.kill()
            except:
                pass

        time.sleep(60)
        db.reset()

if __name__ == "__main__":
    classifier_controller = ClassifierController()

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(currentdir + '/jobs/job_classifier.py' ):
        workingdir = currentdir

    elif os.path.exists(parentdir + '/jobs/job_classifier.py' ):
        workingdir = parentdir


    path_db_cnf = workingdir+"/config/config_db.ini"
    helper = Helper()

    db_cnf = helper.file_to_dict(path_db_cnf)

    db = DB(db_cnf)

    classifier_controller.stop([["chrome", "chromium"], db])

    del helper
    del db
    del classifier_controller
