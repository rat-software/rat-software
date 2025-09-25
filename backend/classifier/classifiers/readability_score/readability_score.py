"""
The `main` function orchestrates the classification process for a classifier by checking for
duplicates, classifying results, and updating the database with classification information.

:param classifier_id: The `classifier_id` is a unique identifier for a specific classifier. It is
used to retrieve and classify results associated with that particular classifier in the database.
:param db: The `db` parameter refers to a Database connection object. This object is used to interact 
with the database where the classification results are stored. It allows performing operations such as
querying for results, inserting classification results, updating records, and checking for duplicates 
in the database.
:param helper: The `helper` parameter is an object that provides additional functionality to the classifier. 
It likely contains methods or attributes that assist in decoding data, handling specific operations, or 
performing other tasks that are necessary for the classification process.

Available data for the classifiers: 
url = data["url"] 
main = data["main"] 
position = data["position"] 
searchengine = data["searchengine"] 
searchengine_title = data["title"] 
searchengine_description = data["description"] 
ip = data["ip"] 
code = helper.decode_code(data["code"]) 
picture = helper.decode_picture(data["bin"]) 
content_type = data["content_type"] 
error_code = data["error_code"] 
status_code = data["status_code"] 
final_url = data["final_url"] 
query = data["query"]

"""

import os
import inspect
import sys

# Add the /classifiers/lib/ directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'libs')))

from lib_db import DB
from lib_helper import Helper
from pathlib import Path


# Determine the directory where this script is located
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# Add the /libs/ directory to the system path to enable imports from that location
sys.path.append(currentdir + "/libs/")

# Import everything from the 'indicators' module
from textanalyzer import *

def main(classifier_id, db, helper, job_server, study_id):
    print("readibility_score")
    print(study_id)
    """
    Main function responsible for classifying results using a specified classifier.

    Args:
        classifier_id (int): The ID of the classifier to use for classification.
        db (DB): The database object used for database operations.
        helper (Helper): Helper object for additional functionality.

    Returns:
        None
    """
    
    def check_for_duplicates(len_duplicates, source_id):
        """
        Checks for duplicate classification results and handles them accordingly.

        Args:
            check_dup: A list of classification results to check for duplicates.

        Returns:
            bool: Returns False if there are more than 1000 duplicates and processing is done; True otherwise.
        """
        if len_duplicates > 1:
            print("duplicate")

            result_ids = db.get_results_result_source(source_id)
            
            # Retrieve existing classifier results and indicators
            for result_id in result_ids:
                insert_classification = False
                result_id = result_id[0]
                classifier_result = db.get_classifier_result(result_id)
                
                if classifier_result:
                    insert_classification = classifier_result[0][0]
                    result_indicators = db.get_indicators(result_id)
                    break
            
            for result_id in result_ids:
                result_id = result_id[0]
                if insert_classification:
                    
                    try:
                        db.update_classification_result(classifier_id, insert_classification, result_id)
                    except Exception as e:
                        pass
                    
                    if db.check_classification_result_not_in_process(classifier_id, result_id):
                        db.insert_classification_result(classifier_id, insert_classification, result_id, job_server)
                        for ri in result_indicators:
                            indicator = ri[2]
                            value = ri[3]
                            if not db.check_indicator_result(classifier_id, result_id, indicator, value):
                                db.insert_indicator(indicator, value, classifier_id, result_id, job_server)
              
            if insert_classification:
                return True
            else:
                return False
      
        else:
            return False

    def classify_results(results):
        """
        Classify results obtained from the database using a specific classifier.

        Args:
            results (list): List of results to classify.

        Returns:
            None
        """
        # Diese innere Funktion wird nicht mehr benötigt, da wir nur einen Indikator haben.
        # def write_indicators_to_db(indicators, result): ...

        # Mark all results as "in process"
        for result in results:
            result_id = result['id']

            if not db.check_classification_result(classifier_id, result_id):
                print("in process")
                db.insert_classification_result(classifier_id, "in process", result_id, job_server)

        for result in results:
            data = {k: v for k, v in result.items()}
            result_id = data["id"]
            print(result_id)
            
            if db.check_classification_result_not_in_process(classifier_id, result_id):
                print("already processed by another instance")
                continue # Skip if already processed by another instance

            code = helper.decode_code(data["code"])
            error_code = data["error_code"]
            status_code = data["status_code"]

            # print(status_code)
            # print(error_code)
            # print(code)


            try:
                if status_code == 200 and not error_code and code:
                    tx = TextAnalyzer()
                    # Die 'analyze'-Methode gibt nun einen einzelnen Wert zurück (Score oder String)
                    analysis_output = tx.analyze(code)

                    # Prüfen, ob das Ergebnis ein numerischer Score ist
                    if isinstance(analysis_output, (int, float)):
                        # 1. Den einzelnen Indikator direkt in die Datenbank schreiben
                        score_value = f"{analysis_output:.2f}"
                        db.insert_indicator("Reading Ease", score_value, classifier_id, result_id, job_server)
                        
                        # 2. Das Klassifikationsergebnis aus dem Score erstellen
                        classification_result = score_value
                    else:
                        # Wenn es ein String ist (z.B. "Not enough content..."), diesen als Ergebnis nutzen
                        # In diesem Fall werden keine Indikatoren geschrieben
                        classification_result = analysis_output
                else:
                    classification_result = 'error'
                
                db.update_classification_result(classification_result, result_id, classifier_id)

            except Exception as e:
                print(f"Error classifying result {result_id}: {e}")
                classification_result = 'classifier_error'
                db.update_classification_result(classification_result, result_id, classifier_id)

    # Retrieve results to be classified from the database using the classifier ID
    results = db.get_results(classifier_id, study_id)
    print(classifier_id)
    print(len(results))
    
    # Process and classify the retrieved results
    classify_results(results)