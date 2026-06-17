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
sys.path.append(currentdir + "/../")

# Import everything from the 'text_analyzer' module
from text_analyzer import *

from classifier import *

class ReadabilityScore(Classifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = Helper()

    def process_result(self, result, indicators):
        """
        Process a single result to extract indicators.

        Args:
            result (object): The result to process.
            helper (object): Helper object for utility functions.

        Returns:
            dict: A dictionary of indicators extracted from the result.
        """
        print("helper list:")
        print(dir(self.helper))
        code = self.helper.decode_code(result["file_path"])
        error_code = result["error_code"]
        status_code = result["status_code"]
        result_id = result["id"]

        print("test_score")

        classification_result = "error"

        if status_code == 200:
            if not error_code:
                if code:
                    try:
                        tx = Text_Analyzer()
                        analysis_output = tx.analyze(code)
                        print("analysis output")
                        print(analysis_output)
                    except Exception as e:
                        print(f"Analyzer exception {e}")

                    # Check if the result is a numerical score
                    if isinstance(analysis_output, (int, float)):
                        # 1. Write the individual indicator directly to the database
                        score_value = f"{analysis_output:.2f}"
                        self.insert_indicator("Reading Ease", score_value, result_id)

                        # 2. Create the classification result from the score
                        classification_result = score_value
                    else:
                        print("NAN")
                        # If it's a string (e.g., "Not enough content..."), use it as the result
                        # In this case, no indicators will be written
                        classification_result = analysis_output
                    self.insert_indicator("classification_result", classification_result, result_id)
                    self.insert_indicator("exclusion_reason", classification_result, result_id)

                else:
                    print("not code")
                    self.insert_indicator("reason", "No content", result_id)
            else:
                print("error code")
                self.insert_indicator("reason", f"Error code {error_code}", result_id)
        else:
            print("not 200")
            self.insert_indicator("reason", f"HTTP error {status_code}", result_id)

        return classification_result


if __name__ == "__main__":
    pass