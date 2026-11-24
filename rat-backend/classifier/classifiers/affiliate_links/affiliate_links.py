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

# Determine the directory where this script is located
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/libs/")
sys.path.append(currentdir + "/../")

from LinkExtractor import extract_affiliate_links, getTextLength
from classifier import *

class AffiliateLinks(Classifier):

    def get_indicators(self, result, helper):
        """
        Extract affiliate link indicators from a single result using LinkExtractor.

        Args:
            result (dict): The result to process.
            helper (object): Helper providing decode_code().

        Returns:
            dict: Indicators (affiliate link count, links, text length).
        """
        indicators = {}

        file_path = result.get("file_path")
        code = helper.decode_code(file_path) if file_path else ""

        if not code:
            indicators['affiliate_links_count'] = 0
            indicators['affiliate_links'] = []
            indicators['text_length'] = 0
            return indicators

        affiliate_links = extract_affiliate_links(code)

        indicators['affiliate_links_count'] = len(affiliate_links)
        indicators['affiliate_links'] = [link['link'] for link in affiliate_links]
        indicators['text_length'] = getTextLength(code)

        return indicators

    def process_result(self, result, indicators):
        """
        Classify a single result based on the extracted affiliate link indicators.

        Args:
            result (object): The result to process.
            indicators (dict): A named list of values that help the classification process.

        Returns:
            str: The classification value for the result.
        """
        classification_result = "error"

        try:
            if indicators and indicators.get('affiliate_links_count', 0) > 0:
                classification_result = "affiliate_links"
            else:
                classification_result = "no_affiliate_links"
        except Exception as e:
            print(f"Classifier exception {e}")

        return classification_result

if __name__ == "__main__":
    pass