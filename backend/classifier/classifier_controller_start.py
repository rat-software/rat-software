"""
ClassifierController

This class represents a controller for starting the classifier and resetting jobs.

Methods:
    __init__(): Initializes the ClassifierController object.
    __del__(): Destructor for the ClassifierController object.
    start(workingdir): Starts the classifier and resets jobs.

Args:
    workingdir (str): The working directory.

Returns:
    None

Example:
    classifier_controller = ClassifierController()
    classifier_controller.start(workingdir)
    del classifier_controller
"""

# Processing libraries
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

    def start(self, workingdir):
        """
        Start the classifier and reset jobs.

        Args:
            workingdir (str): The working directory.

        Returns:
            None
        """        
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
