"""
The `main` function orchestrates the classification process for a classifier by checking for
duplicates, classifying results, and updating the database with classification information.

:param classifier_id: The `classifier_id` is a unique identifier for a specific classifier.
:param db: The `db` parameter refers to a Database connection object.
:param helper: The `helper` parameter provides additional functionality to decode data.
:param job_server: Identifier for the current server instance.
:param study_id: The ID of the current study.

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

def main(classifier_id, db, helper, job_server, study_id):
    """
    Main function responsible for classifying results using a specified classifier.
    """
    
    def check_for_duplicates(check_dup, source_id):
        """
        Check for duplicate classification results and update the database accordingly.
        """
        # Check if the list of duplicates is too large to handle in bulk
        if len(check_dup) > 1000:
            # Retrieve potential duplicate sources from the database
            result_sources = db.duplicate_classification_result(source_id)
            insert_classification = False

            for result_source in result_sources:
                rs = result_source[0]
                classifier_result = db.get_classifier_result(rs)

                if classifier_result:
                    if not insert_classification:
                        # Mark the classification for insertion
                        insert_classification = classifier_result[0][0]
                        result_indicators = db.get_indicators(rs)

                    # Insert classification result if not already present
                    # Note: For duplicate bulk inserts, we don't need strict atomic locking 
                    # since they are just copies of an already processed result.
                    if not db.check_classification_result(classifier_id, rs):
                        db.insert_classification_result(classifier_id, insert_classification, rs, job_server)

                    # Insert indicators if they don't exist
                    for ri in result_indicators:
                        indicator, value = ri[1], ri[2]
                        if not db.check_indicator_result(classifier_id, rs, indicator, value) and indicator and value:
                            db.insert_indicator(indicator, value, classifier_id, rs, job_server)

            return False
        else:
            return True

    def classify_results(results):
        """
        Classify results obtained from the database using a specific classifier.
        Uses atomic database constraints to prevent race conditions across multiple servers.
        """
        def write_indicators_to_db(indicators, result_id):
            """
            Write indicators to the database for a specific result.
            """
            for key, ind in indicators.items():
                indicator = key
                # Convert indicators to string format for database insertion
                if isinstance(ind, (list, dict)):
                    insert_result = ", ".join(ind) if isinstance(ind, list) else ", ".join([str(v) for v in ind.values()])
                else:
                    insert_result = str(ind)

                # Insert indicator into the database
                db.insert_indicator(indicator, insert_result, classifier_id, result_id, job_server)

        for result in results:
            data = {k: v for k, v in result.items()}
            result_id = data['id']
            source_id = data.get("source")

            # ---------------------------------------------------------
            # ATOMIC CONCURRENCY CHECK (Crucial for Multi-Server Setups!)
            # ---------------------------------------------------------
            # Try to insert "in process" directly into the DB.
            # If it returns False, another instance just claimed it or it's already processed.
            if not db.insert_classification_result(classifier_id, "in process", result_id, job_server):
                print(f"Result {result_id} already locked or processed by another instance. Skipping.")
                continue # Safely skip to the next document

            # ---------------------------------------------------------
            # IF WE REACH HERE, THIS SERVER OWNS THE JOB!
            # ---------------------------------------------------------

            # Check for duplicates before proceeding with heavy processing
            check_dup = db.check_source_duplicates(source_id)
            if check_for_duplicates(check_dup, source_id):
                classification_result = ''
                indicators = {}

                try:
                    # =========================================================
                    # Start your custom code here
                    # =========================================================
                    
                    # Load the code/picture securely
                    # code = helper.decode_code(data.get("file_path"))
                    # picture = helper.decode_picture(data.get("file_path"))

                    # classification_result = custom_classify(result, helper)
                    # indicators = calculate_indicators(result, helper)

                    # Example fallback result if nothing is implemented yet:
                    # classification_result = 'processed' 

                    # =========================================================
                    # End of your custom code
                    # =========================================================

                    # Write calculated indicators to the database
                    write_indicators_to_db(indicators, result_id)
                    
                    # Update the classification result in the database 
                    # (Order: Value, Result_ID, Classifier_ID)
                    db.update_classification_result(classification_result, result_id, classifier_id)

                except Exception as e:
                    print(f"Critical error executing custom classifier logic for result {result_id}: {str(e)}")
                    # Failsafe: Prevent the job from being stuck as "in process" forever
                    db.update_classification_result('classifier_error', result_id, classifier_id)

    # Retrieve results to be classified from the database using the classifier ID and study ID
    results = db.get_results(classifier_id, study_id)
    print(f"Found {len(results)} pending results for classifier {classifier_id}")
    
    # Process and classify the retrieved results
    classify_results(results)