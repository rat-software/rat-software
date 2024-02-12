"""
Class for loading and running classifiers.

Methods:
    __init__: Initialize the Classifier object.
    __del__: Destructor for the Classifier object.
    load_classifier: Load and run classifiers.

Args:
    classifiers (list): List of classifiers.
    db (object): Database object.
    helper (object): Helper object.

"""

import json
import importlib

import os
import sys
import inspect

from libs.lib_helper import *
from libs.lib_db import *

class Classifier:

    def __init__(self):
        """
        Initialize the Classifier object.
        """        
        self = self

    def __del__(self):
        """
        Destructor for the Classifier object.
        """        
        print('Classifier object destroyed')


    def load_classifier(self, classifiers, db, helper):
        """
        Load and run classifiers.

        Args:
            classifiers (list): List of classifiers.
            db (object): Database object.
            helper (object): Helper object.

        Returns:
            None
        """        
        for c in classifiers:
            classifier_id = c['id']
            classifier_name = c['name']
            mod_folder = "classifiers."+classifier_name+"."+classifier_name
            module = importlib.import_module(mod_folder)
            module.main(classifier_id, db, helper)

if __name__ == "__main__":

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    helper = Helper()

    db_cnf = currentdir+"/../config/config_db.ini"

    db_cnf = helper.file_to_dict(db_cnf)

    db = DB(db_cnf)

    classifiers = db.get_classifiers()

    classifier = Classifier()

    classifier.load_classifier(classifiers, db, helper)
