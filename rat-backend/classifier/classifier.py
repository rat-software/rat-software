"""
Module for loading and running classifiers.

Classes:
    Classifier: A class for loading and running classifiers.

Functions:
    main: Main function to initialize helper, database, and run classifiers.

Args:
    classifiers (list): List of classifiers.
    db (object): Database object.
    helper (object): Helper object.
"""

import importlib
from pathlib import Path
import json
from libs.lib_helper import Helper
from libs.lib_db import DB

class Classifier:
    """
    A class used to load and run classifiers.

    Methods:
        load_classifier: Load and run classifiers.
    """

    def load_classifier(self, classifiers, db, helper, job_server):
        """        
        Load and run classifiers.

        Args:
            classifiers (list): List of classifiers to be loaded and run.
            db (object): Database object to interact with the database.
            helper (object): Helper object for utility functions.

        Returns:
            None
        """
        # Iterate over each classifier in the list
        for c in classifiers:
            print(c)
    
            # Dynamically import the classifier module based on the classifier name
            module = importlib.import_module(f"classifiers.{c['name']}.{c['name']}")
            # Call the main function of the imported module with classifier ID, db, and helper as arguments
            module.main(c['id'], db, helper, job_server, c['study'])
            #db.deleteClassifierDuplicates()


def main():
    """
    Main function to initialize helper, database, and run classifiers.

    This function initializes the helper and database objects, retrieves the list of classifiers
    from the database, and then uses the Classifier class to load and run each classifier.

    Args:
        None

    Returns:
        None
    """
    # Initialize the Helper object
    helper = Helper()
    
    # Get the current directory of the script
    currentdir = Path(__file__).resolve().parent
    # Construct the path to the database configuration file
    path_db_cnf = currentdir / ".." / "config" / "config_db.ini"
    
    # Initialize the DB object with the configuration loaded from the file
    db = DB(helper.file_to_dict(path_db_cnf))

    # Construct the path to the sources configuration file
    path_sources_cnf = currentdir / ".." / "config" / "config_sources.ini"

    # Open the JSON file for reading with UTF-8 encoding
    with open(path_sources_cnf, encoding="utf-8") as f:
            # Load the JSON content into a dictionary
        data = json.load(f)
    
    job_server = data['job_server']
    
    # Retrieve the list of classifiers from the database
    classifiers = db.get_classifiers()
    
    # Create a Classifier object and load the classifiers
    Classifier().load_classifier(classifiers, db, helper, job_server)

if __name__ == "__main__":
    main()
