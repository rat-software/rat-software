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

def main():
    """
    Main function responsible for classifying results using a specified classifier.

    Args:
        classifier_id (int): The ID of the classifier to use for classification.
        db (DB): The database object used for database operations.
        helper (Helper): Helper object for additional functionality.

    Returns:
        None
    """
    
    def check_for_duplicates(check_dup):
        pass
    def classify_results(results):
        """
        Classify results obtained from the database using a specific classifier.

        Args:
            results (list): List of results to classify.

        Returns:
            None
        """
        def write_indicators_to_db(indicators, result):
            """
            Write indicators to the database for a specific result.

            Args:
                indicators (dict): Dictionary of indicators to write.
                result (dict): The result to associate the indicators with.

            Returns:
                None
            """
            pass

        for result in results:
            data = {k: v for k, v in result.items()}
            result_id = data["id"]
            url = data["url"]
            main = data["main"]
            position = data["position"]
            searchengine_title = data["title"]
            searchengine_description = data["description"]
            ip = data["ip"]
            code = helper.decode_code(data["code"])
            picture = helper.decode_picture(data["bin"])
            content_type = data["content_type"]
            error_code = data["error_code"]
            status_code = data["status_code"]
            final_url = data["final_url"]
            source_id = data["source"]

            # Start your custom code here for calculating indicators and classifying a result

            # Custom code:

            print(url)
            classification_result = "Readability could not be calculated"
            try:
                tx = TextAnalyzer()
                indicators = tx.analyze(code)

                print(indicators)
               

                if indicators["Reading Ease"] >= 70 and indicators["Grade"] <= 6:
                    classification_result = 'Very High Readability'

                elif indicators["Reading Ease"] >= 70 and indicators["Grade"] <= 12:
                    classification_result = 'High Readability'

                elif indicators["Reading Ease"] >= 30 and indicators["Grade"] <= 69 and indicators["Grade"] <= 12 and indicators["Grade"] >= 6:
                    classification_result = 'Medium Readability'

                else:
                    classification_result = 'Low Readability'
            
            except Exception as e:
                print(str(e))
                pass

            
            print(classification_result)
            # End of your custom code

             

    # Retrieve results to be classified from the database using the classifier ID
    results = db.get_results_test()
    # Process and classify the retrieved results
    classify_results(results)

if __name__ == "__main__":

    # Initialize the Helper object
    helper = Helper()
    
    # Get the current directory of the script
    currentdir = Path(__file__).resolve().parent
    # Construct the path to the database configuration file
    path_db_cnf = currentdir / "../../.." / "config" / "config_db.ini"
    print(path_db_cnf)
    
    # Initialize the DB object with the configuration loaded from the file
    db = DB(helper.file_to_dict(path_db_cnf))    
    main()