from flask import json
import os
import inspect
import sys

# Import path setup from original script
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/../libs/")

from lib_helper import Helper


class Classifier:
    def __init__(self, classifier_id: int = None, db=None, job_server: str = None):
        self.helper = Helper()
        self.classifier_id = classifier_id
        self.db = db
        self.job_server = job_server

    def insert_indicator(self, key, value, result_id):
        """Insert an indicator into the database"""
        db = self.db
        classifier_id = self.classifier_id
        job_server = self.job_server
        db.insert_indicator(key, value, classifier_id, result_id, job_server)
    
    def classify_results(self, results, helper):
        """Classify results and update database with scores and indicators"""
        result_counter = len(results)

        for result in results:
            data = {k: v for k, v in result.items()}
            result_id = data["id"]

            result_counter -= 1
            print(result_counter)
            print(result_id)

            try:
                
                # 1. Check if the result is already fully processed (has a final score)
                if self.db.check_classification_result_not_in_process(self.classifier_id, result_id):
                    print(f"Result {result_id} is already finished.")
                    continue

                # 2. Check if another server is currently processing it (has "in process" status)
                if self.db.check_classification_result(self.classifier_id, result_id):
                    print(f"Result {result_id} is already being processed by another server")
                    continue

                # 3. If neither applies, claim the result by inserting "in process"
                self.db.insert_classification_result(self.classifier_id, "in process", result_id, self.job_server)
                
                # ---------------------------------------------------------

                try:
                    indicators = self.get_indicators(data, helper)

                    if indicators:

                        # Save indicators to the database
                        for key, value in indicators.items():
                            if isinstance(value, (list, dict)):
                                value_str = json.dumps(value)
                            else:
                                value_str = str(value)
                            self.db.insert_indicator(key, value_str, self.classifier_id, result_id, self.job_server)
                        # Check if excluded
                        if indicators['excluded'] == True:
                            self.db.update_classification_result('excluded', result_id, self.classifier_id)
                            self.db.insert_indicator('exclusion_reason', indicators['reason'],
                                                self.classifier_id, result_id, self.job_server)
                            self.db.insert_indicator('content_type', indicators['content_type'],
                                                self.classifier_id, result_id, self.job_server)
                            continue
                    # Calculate classification
                    classification_value = self.process_result(result, indicators)

                    self.db.update_classification_result(classification_value, result_id, self.classifier_id)

                except Exception as e:
                    print(f"Error in classification: {str(e)}")
                    self.db.update_classification_result('error', result_id, self.classifier_id)

            except Exception as e:
                print(f"Error in result check/claim: {str(e)}")
                self.db.update_classification_result('error', result_id, self.classifier_id)
    
    def process_result(self, result, indicators=None):
        """
        Process a single result to extract indicators.

        Args:
            result (object): The result to process.
            indicators (dict): Indicators to help classification.

        Returns:
            dict: A dictionary of indicators extracted from the result.
        """
        raise NotImplementedError("This method should be implemented by subclasses to process results and extract indicators.")
    
    def get_indicators(self, result, helper) -> dict:
        """
        Extract indicators from a single result.

        Args:
            result (object): The result to extract indicators from.
            helper (object): Helper object for utility functions.

        Returns:
            dict: A dictionary of indicators extracted from the result.

        This method should be implemented if you would like to use a list of indicators for your classification and/or store them for future use.
        """
        indicators = {}
        return indicators
