"""
Module for loading and running classifiers.

Classes:
    ClassifierRunner: A class for loading and running classifiers.

Functions:
    main: Main function to initialize helper, database, and run classifiers.
"""

import importlib
from pathlib import Path
import json
from libs.lib_helper import Helper
from libs.lib_db import DB

class ClassifierRunner:
    """
    A class used to load and run classifiers.

    Methods:
        load_classifier: Central method to flag failed sources and execute classifiers.
    """

    def load_classifier(self, classifiers, db, helper, job_server):
        """        
        Load and run classifiers. First performs a pre-flight check to flag permanently 
        failed scraping sources, preventing infinite processing loops across multiple classifiers.

        Args:
            classifiers (list): List of classifiers to be loaded and run.
            db (object): Database object to interact with the database.
            helper (object): Helper object for utility functions.
            job_server (str): Identifier of the processing server.

        Returns:
            None
        """
        # Iterate over each classifier in the list
        for c in classifiers:
            print(c)
            
            # Central Pre-Flight Check: Identify results whose scraping attempts permanently failed 
            # (progress = -1 and counter >= max_counter) and mark them as 'source_failed' in the database.
            # This ensures that individual classifiers skip unscrapable URLs and do not stall the pipeline.
            db.flag_dead_sources(c['id'], c['study'], job_server)
    
            # Dynamically import the classifier module based on the classifier name
            module = importlib.import_module(f"classifiers.{c['name']}.{c['name']}")
            # Call the main function of the imported module with classifier ID, db, and helper as arguments
            classifier_name = c['name']
            classifier_id = c['id']
            if(classifier_name):
                print(f"Running classifier: {classifier_name}")
                class_name = helper.to_camel_case(classifier_name)
                try:
                    classifier_class = getattr(module, class_name)
                    classifier = classifier_class()
                    # Get results and start classification
                    results = db.get_results(classifier_id, c['study'])
                    print(results)
                    print(f"Processing {len(results)} results for classifier {classifier_id}")
                    classifier.classify_results(results, classifier_id, db, job_server, classifier, helper)
                except Exception as e:
                    print(f"Error occurred while running classifier {class_name}: {e}")
                    print(f"Classifier not found: {class_name}. Trying the old way.")
                    module.main(c['id'], db, helper, job_server, c['study'])
                    #db.deleteClassifierDuplicates()
            else:
                print("Classifier name not provided. Cannot run classifier.")

def main():
    """
    Main function to initialize helper, database, and run classifiers.

    This function initializes the helper and database objects, extracts centralized scraper configuration 
    parameters (such as max retries/counter), retrieves the list of classifiers from the database, 
    and invokes the Classifier manager to process records.

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
    
    # Construct the path to the sources configuration file
    path_sources_cnf = currentdir / ".." / "config" / "config_sources.ini"

    # Open the sources configuration file for reading with UTF-8 encoding
    with open(path_sources_cnf, encoding="utf-8") as f:
        # Load the configuration content into a dictionary
        data = json.load(f)
    
    # Extract operational configurations from the file
    job_server = data.get('job_server', 'unknown_server')
    refresh_time = data.get('refresh_time', 48)
    
    # Read the global maximum retry boundary ('counter') from the configuration file (defaulting to 3 if missing)
    max_counter = data.get('counter', 3)
    
    # Initialize the DB object with the connection credentials and synchronization parameters.
    # Passing the max_counter allows the central DB instance to know the exact failure threshold.
    db = DB(helper.file_to_dict(path_db_cnf), job_server, refresh_time, max_counter)
    
    # Retrieve the list of active classifiers from the database
    classifiers = db.get_classifiers()
    
    # Create a Classifier object and load the classifiers
    ClassifierRunner().load_classifier(classifiers, db, helper, job_server)

if __name__ == "__main__":
    main()