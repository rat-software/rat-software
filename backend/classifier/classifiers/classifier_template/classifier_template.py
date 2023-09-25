"""
Example classifier with all relevant functions to work with the scraped data.
\nTutorial to create your classifier:
1. First item
2. Second item
"""


class Classifier:

    """Classifier"""
    args: list
    """The args for the controller to stop it
    \nparam: args[0]:list = name of browser process (chrome, chromium, firefox)
    \nparam: db:object = Database object
    """

    def __init__(self, classifier_id, db, helper):
        self = self
        self.classifier_id = classifier_id
        self.db = db
        self.helper = helper

    def __del__(self):
        print('Classifier object destroyed')

    def get_results(self):
        results = self.db.get_results(self.classifier_id)
        return results

    def classifiy_results(self, results):

        """
        Function to classify results. First step is storing some placeholder progresses in the database for the classification_results before reading the available data for custom classifiers.
        While the function is developed to run parallel several steps are taken to ensure that no duplicates will be saved. There are also loops to check if results with same data are classified already. If that's the case, the script copies
        the stored results and assigns them to the result_id. Such checks are also done for indicators. Some strict rules are applied here to work just with data which were scraped successfully. To check that just documents with a server status code of 200
        will be classified.
        """

        data = {}

        for result in results:
            '''Function to block a result to classify'''
            result_id = result['id']
            db.insert_classification_result(classifier_id, "in process", result_id)

        for result in results:
            data = {}

            for k,v in result.items():
                data.update({k: v})

        if data:
            '''Available data from scraping to work with'''
            result = data["id"]
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
            source_id = data["source"]
            check_dup = db.check_source_dup(source_id)

            '''Check whether the result has already been classified.'''

            if len(check_dup) > 1:
                result_sources = db.duplicate_classification_result(source_id)

                for result_source in result_sources:
                    rs = result_source[0]
                    classifier_result = db.get_classifier_result(rs)
                    if classifier_result:
                        result_indicators = db.get_indicators(rs)
                        break

                for result_source in result_sources:
                    rs = result_source[0]
                    classifier_result = db.get_classifier_result(rs)
                    if classifier_result:
                        insert_classification = classifier_result[0][0]
                        break


                for result_source in result_sources:
                    rs = result_source[0]
                    classifier_result = db.get_classifier_result(rs)

                    if not classifier_result:
                        if not db.check_classification_result(classifier_id, rs):
                            db.insert_classification_result(classifier_id, insert_classification, rs)

                    if not classifier_result:
                        for ri in result_indicators:
                            indicator = ri[1]
                            value = ri[2]
                            if not db.check_indicator_result(classifier_id, rs):
                                db.insert_indicator(indicator, value, classifier_id, rs)

                db.update_classification_result(classifier_id, insert_classification, result_id)
                
                '''Define your indicators and classification rules here'''

            try:

                if status_code == 200 and len(error_code) == 0 and not db.check_classification_result(classifier_id, result):


                    '''A very simple example for creating an indicator from the data and to use it to classify a result'''

                    indicator = "code_length"

                    if len(code) > 1000:
                        insert_result = 1
                        classification_result = "Long Code"
                    else:
                        insert_result = 0
                        classification_result = "Short Code"

                    db.insert_indicator(indicator, insert_result, classifier_id, result) #function to write the indicator to the db

                    db.update_classification_result(classifier_id, classification_result, result) #function to write the classifier result to the db
            except:
                pass

'''Example main function to read all available data from the database'''

def main(classifier_id, db, helper):

    '''Initialize classifier object'''
    classifier_obj = Classifier(classifier_id, db, helper)

    '''Get results from Database'''
    results = classifier_obj.get_results()

    '''Classify results from Database'''
    classifier_obj.classifiy_results(results)
