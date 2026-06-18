from flask import json


class Classifier:
    def __init__(self, name: str):
        self.name = name
    
    def classify_results(self, results, classifier_id, db, job_server, scorer, helper):
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
                if db.check_classification_result_not_in_process(classifier_id, result_id):
                    print(f"Result {result_id} is already finished.")
                    continue

                # 2. Check if another server is currently processing it (has "in process" status)
                if db.check_classification_result(classifier_id, result_id):
                    print(f"Result {result_id} is already being processed by another server")
                    continue

                # 3. If neither applies, claim the result by inserting "in process"
                db.insert_classification_result(classifier_id, "in process", result_id, job_server)
                
                # ---------------------------------------------------------

                try:
                    indicators = self.process_result(data, helper)

                    if indicators:
                        # Check if it's not HTML
                        if not indicators.get('is_html', True):
                            # Mark non-HTML documents as excluded from SEO scoring
                            db.update_classification_result('excluded', result_id, classifier_id)
                            db.insert_indicator('exclusion_reason', indicators['reason'],
                                            classifier_id, result_id, job_server)
                            db.insert_indicator('content_type', indicators['content_type'],
                                            classifier_id, result_id, job_server)
                            continue

                        # Calculate SEO score
                        score_results = scorer.calculate_score(indicators)

                        # Update classification result
                        classification_value = f"{score_results['total_score']}"
                        db.update_classification_result(classification_value, result_id, classifier_id)

                        # Store indicators
                        for key, value in indicators.items():
                            if isinstance(value, (list, dict)):
                                value_str = json.dumps(value)
                            else:
                                value_str = str(value)
                            db.insert_indicator(key, value_str, classifier_id, result_id, job_server)

                        # Store category scores
                        for category, score in score_results['category_scores'].items():
                            db.insert_indicator(f"category_{category}", str(score),
                                            classifier_id, result_id, job_server)

                        # Store analysis explanation
                        db.insert_indicator('analysis_explanation', score_results['explanation'],
                                        classifier_id, result_id, job_server)

                        # Store classification
                        classification = scorer.get_classification(score_results['total_score'])
                        db.insert_indicator('seo_classification', classification,
                                        classifier_id, result_id, job_server)

                    else:
                        db.update_classification_result('error', result_id, classifier_id)

                except Exception as e:
                    print(f"Error in classification: {str(e)}")
                    db.update_classification_result('error', result_id, classifier_id)

            except Exception as e:
                print(f"Error in classification: {str(e)}")
                db.update_classification_result('error', result_id, classifier_id)
    
    def process_result(self, result, helper):
        """
        Process a single result to extract indicators.

        Args:
            result (object): The result to process.
            helper (object): Helper object for utility functions.

        Returns:
            dict: A dictionary of indicators extracted from the result.
        """
        raise NotImplementedError("This method should be implemented by subclasses to process results and extract indicators.")
        # Placeholder for actual processing logic
        """indicators = {
            "indicator_1": helper.extract_indicator_1(result),
            "indicator_2": helper.extract_indicator_2(result),
            # Add more indicators as needed
        }
        return indicators"""

