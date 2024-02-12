"""
Class for resetting the classifier.

Methods:
    __init__: Initialize the ClassifierReset object.
    __del__: Destructor for the ClassifierReset object.
    reset: Reset the classifier.

Args:
    db (object): Database object.
"""

from libs.lib_helper import *
from libs.lib_db import *

from datetime import datetime

import json

import os
import inspect

class ClassifierReset:

    def __init__(self, db):
        """
        Initialize the ClassifierReset object.

        Args:
            db (object): Database object.
        """        
        self = self
        self.db = db

    def __del__(self):
        """
        Destructor for the ClassifierReset object.
        """        
        print('ClassifierReset object destroyed')

    def reset(self, db):
        """
        Reset the classifier.

        Args:
            db (object): Database object.

        Returns:
            None
        """        
        db.reset()

if __name__ == "__main__":

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    db_cnf = currentdir+"/../config/config_db.ini"
     
    helper = Helper()

    db_cnf = helper.file_to_dict(db_cnf)

    db = DB(db_cnf)

    classifier_reset = ClassifierReset(db)
    classifier_reset.reset(db)

    del db
    del classifier_reset
