"""
Module for resetting the classifier.

Classes:
    ClassifierReset: A class for resetting the classifier.

Methods:
    __init__: Initialize the ClassifierReset object.
    reset: Reset the classifier.

Args:
    db (object): Database object.
"""

from libs.lib_helper import Helper
from libs.lib_db import DB
import os
import inspect
import json

class ClassifierReset:
    """
    A class used to reset the classifier.

    Methods:
        __init__: Initialize the ClassifierReset object.
        reset: Reset the classifier.
    """

    def __init__(self, db):
        """
        Initialize the ClassifierReset object.

        Args:
            db (object): Database object to interact with the database.
        """        
        self.db = db  # Assign the database object to an instance variable

    def reset(self, job_server):
        """
        Reset the classifier.

        Returns:
            None
        """        
        self.db.reset(job_server)  # Call the reset method on the database object

if __name__ == "__main__":
    # Get the current directory of the script
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    # Get the parent directory of the current directory
    parentdir = os.path.dirname(currentdir)

    # Path to the database configuration file
    db_cnf_path = os.path.join(currentdir, "..", "config", "config_db.ini")

    # Initialize the Helper object
    helper = Helper()

    # Convert the configuration file to a dictionary
    db_cnf = helper.file_to_dict(db_cnf_path)

    # Initialize the DB object with the configuration dictionary
    db = DB(db_cnf)

    # Load sources configuration
    path_sources_cnf = os.path.join(currentdir, "../config/config_sources.ini")
    sources_cnf = helper.file_to_dict(path_sources_cnf)
    job_server = sources_cnf['job_server']    
    


    # Create a ClassifierReset object with the DB object
    classifier_reset = ClassifierReset(db)
    # Call the reset method to reset the classifier
    classifier_reset.reset(job_server)
