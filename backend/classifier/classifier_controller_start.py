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

    """SourcesController"""
    args: list
    """The args for the controller to stop it
    \nparam: args[0]:list = name of browser process (chrome, chromium, firefox)
    \nparam: db:object = Database object
    """

    def __init__(self):
        self = self

    def __del__(self):
        print('Classifier Controller object destroyed')

    def start(self, workingdir):

        def classifier():
            call(["python", workingdir + "/jobs/job_classifier.py"])

        def reset():
            call(["python", workingdir + "/jobs/job_reset_classifier.py"])

        process1 = threading.Thread(target=classifier)
        process1.start()

        process2 = threading.Thread(target=reset)
        process2.start()


if __name__ == "__main__":
    classifier_controller = ClassifierController()

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(currentdir + '/jobs/job_classifier.py' ):
        workingdir = currentdir

    elif os.path.exists(parentdir + '/jobs/job_classifier.py' ):
        workingdir = parentdir

    classifier_controller.start(workingdir)
    del classifier_controller
