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
code = helper.decode_code(data["file_path"])
picture = helper.decode_picture(data["file_path"])
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

# Import everything from the 'text_analyzer' module
from text_analyzer import *

def main(classifier_id, db, helper, job_server, study_id):
    """
    Main function responsible for classifying results using a specified classifier.

    Args:
        classifier_id (int): The ID of the classifier to use for classification.
        db (DB): The database object used for database operations.
        helper (Helper): Helper object for additional functionality.
        job_server (str): Identifier of the processing server.
        study_id (int): The ID of the study currently being processed.

    Returns:
        None
    """
    print(f"Executing readability_score for Study ID: {study_id}")

    def classify_results(results):
        """
        Classify results obtained from the database using a specific classifier.
        Uses atomic database constraints to prevent race conditions across multiple servers.

        Args:
            results (list): List of results to classify.

        Returns:
            None
        """
        for result in results:
            result_id = result['id']

            # ATOMIC LOCK ATTEMPT: Try to insert "in process" directly into the DB.
            # If it returns False, another instance just claimed it or it's already processed.
            if not db.insert_classification_result(classifier_id, "in process", result_id, job_server):
                print(f"Result {result_id} already locked or processed by another instance. Skipping.")
                continue # Safely skip to the next document

            # IF WE REACH HERE, THIS SERVER OWNS THE JOB!
            data = {k: v for k, v in result.items()}
            code = helper.decode_code(data["file_path"])
            error_code = data["error_code"]
            status_code = data["status_code"]

            try:
                # Proceed only if the page loaded successfully and HTML code exists
                if status_code == 200 and not error_code and code:
                    tx = Text_Analyzer()
                    analysis_output = tx.analyze(code)

                    # Check if the analysis successfully returned a numerical score
                    if isinstance(analysis_output, (int, float)):
                        # 1. Write the individual indicator directly to the database
                        score_value = f"{analysis_output:.2f}"
                        db.insert_indicator("Reading Ease", score_value, classifier_id, result_id, job_server)
                        
                        # 2. Assign the numerical score as the main classification result
                        classification_result = score_value
                    else:
                        # If it returned a string (e.g., "Language 'bn' not supported" or "Not enough text")
                        # Save the exact reason as an indicator to keep the DB clean!
                        db.insert_indicator("exclusion_reason", str(analysis_output), classifier_id, result_id, job_server)
                        
                        # Set the main classification result to a standardized error flag
                        classification_result = 'error'
                else:
                    classification_result = 'error'
                
                # Update the database with the final score or error flag
                db.update_classification_result(classification_result, result_id, classifier_id)

            except Exception as e:
                print(f"Error classifying result {result_id}: {e}")
                classification_result = 'classifier_error'
                db.update_classification_result(classification_result, result_id, classifier_id)

    # Retrieve results to be classified from the database using the classifier ID
    results = db.get_results(classifier_id, study_id)
    print(f"Found {len(results)} pending results for classifier {classifier_id}")
    
    # Process and classify the retrieved results
    classify_results(results)