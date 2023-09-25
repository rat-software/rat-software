import json
import importlib

import os
import sys
import inspect

from libs.lib_helper import *
from libs.lib_db import *

class Classifier:

    def __init__(self):
        self = self

    def __del__(self):
        print('Classifier object destroyed')


    def load_classifier(self, classifiers, db, helper):
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
