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
            db (DB): Database object to interact with the database.
            helper (Helper): Helper object for utility functions.
            job_server (str): Identifier of the processing server.

        Returns:
            None
        """
        # Iterate over each classifier in the list
        for c in classifiers:
            import time
            import traceback
            
            print("\n" + "="*40)
            print(f"Starte Verarbeitung für Studie {c['study']} (Classifier: {c['name']})")
            
            # --- 1. Dead Sources ---
            t0 = time.time()
            try:
                db.flag_dead_sources(c['id'], c['study'], job_server)
                print(f"⏱️ Zeit für 'flag_dead_sources': {time.time() - t0:.2f} Sekunden")
            except Exception as e:
                print(f"❌ Fehler in flag_dead_sources: {e}")
                
            # --- 2. IMPORT (Hier passiert dein Absturz!) ---
            try:
                module = importlib.import_module(f"classifiers.{c['name']}.{c['name']}")
            except Exception as e:
                print(f"\n🔥 FATALER IMPORT-FEHLER BEI {c['name']} 🔥")
                print(f"Grund: {e}")
                print(traceback.format_exc())
                continue  # Überspringt diesen Classifier und macht mit dem nächsten weiter
                
            # --- 3. Klassifizierung ---
            classifier_name = c['name']
            if(classifier_name):
                class_name = helper.to_camel_case(classifier_name)
                try:
                    classifier_class = getattr(module, class_name)
                    classifier = classifier_class(classifier_id=c['id'], db=db, job_server=job_server)
                    
                    t1 = time.time()
                    results = db.get_results(c['id'], c['study'])
                    print(f"⏱️ Zeit für 'get_results' ({len(results)} gefunden): {time.time() - t1:.2f} Sekunden")
                    
                    t2 = time.time()
                    print(f"🚀 Starte eigentliche Klassifizierung...")
                    classifier.classify_results(results, helper)
                    print(f"⏱️ Zeit für Klassifizierung: {time.time() - t2:.2f} Sekunden")
                    
                except Exception as e:
                    print(f"\n❌ FEHLER WÄHREND DER AUSFÜHRUNG BEI {c['name']}:")
                    print(traceback.format_exc())

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
    
    # Retrieve the list of active classifiers from the database
    classifiers = db.get_classifiers()
    
    # Create a Classifier object and load the classifiers
    ClassifierRunner().load_classifier(classifiers, db, helper, job_server)

if __name__ == "__main__":
    main()