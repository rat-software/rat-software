import os
import inspect
import sys

#duplicates [[983], [1165]]

# Determine the directory where this script is located
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# Add the /libs/ directory to the system path to enable imports from that location
sys.path.append(currentdir + "/libs/")

# Import everything from the 'indicators' module
from indicators import *

def main(classifier_id, db, helper, job_server, study_id):
    print("seo rule based")
    print(study_id)
    """
    Main function for the classifier, which processes and classifies web results.

    Args:
        classifier_id (int): The ID of the classifier to use for classification.
        db: An instance of the DB class for interacting with the database.
        helper: An instance of the helper class for utility functions.

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
        print(len_duplicates)
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
                    except:
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
        Classifies the provided results based on various indicators and updates the database.

        Args:
            results (list): A list of results to classify.

        Returns:
            None
        """

        def write_indicators_to_db(indicators, result):
            """
            Writes classification indicators to the database.

            Args:
                indicators (dict): Dictionary of indicators to be written.
                result: The result associated with these indicators.

            Returns:
                None
            """
            for key, value in indicators.items():
                if isinstance(value, (list, dict)):
                    insert_result = ", ".join(value) if isinstance(value, list) else ", ".join([f"{k}: {v}" for k, v in value.items()])
                else:
                    insert_result = str(value)
                db.insert_indicator(key, insert_result, classifier_id, result, job_server)

        # Mark all results as "in process"
        for result in results:
            result_id = result['id']
            if not db.check_classification_result(classifier_id, result_id):
                print("in process")
                db.insert_classification_result(classifier_id, "in process", result_id, job_server)

        

        for result in results:
            data = {k: v for k, v in result.items()}
            source_id = data["source"]
            result_id = data["id"]
            sources_duplicates = db.check_source_duplicates(source_id)

            print(result_id)
            print(classifier_id)





            if not db.check_classification_result_not_in_process(classifier_id, result_id):
                classification_result = 'error'
                indicators = {}


                try:
                    
                    url = data["url"]
                    main = data["main"]
                    code = helper.decode_code(data["code"])
                    error_code = data["error_code"]
                    status_code = data["status_code"]
                    query = data["query"]
                    if status_code == 200 and not error_code:
                        # Identify plugins from the code
                        plugins = identify_plugins(code)
                        indicators.update({'tools analytics': plugins['tools analytics'],
                                        'tools seo': plugins['tools seo'],
                                        'tools caching': plugins['tools caching'],
                                        'tools social': plugins['tools social'],
                                        'tools ads': plugins['tools ads']})

                        # Count various tools and sources
                        tools_analytics = len(plugins['tools analytics'])
                        tools_seo = len(plugins['tools seo'])
                        tools_caching = len(plugins['tools caching'])
                        tools_social = len(plugins['tools social'])
                        tools_ads = len(plugins['tools ads'])

                        lists = identify_sources(main)
                        indicators.update({'ads': lists['ads'],
                                        'company': lists['company'],
                                        'seo_customers': lists['seo_customers'],
                                        'news': lists['news'],
                                        'not_optimized': lists['not_optimized'],
                                        'search_engine_services': lists['search_engine_services'],
                                        'shops': lists['shops']})

                        sources_ads = len(lists['ads'])
                        sources_company = len(lists['company'])
                        sources_customers = len(lists['seo_customers'])
                        sources_news = len(lists['news'])
                        sources_not_optimized = len(lists['not_optimized'])
                        sources_services = len(lists['search_engine_services'])
                        sources_shops = len(lists['shops'])

                        robots_txt = identify_robots_txt(main)
                        indicators.update({'robots_txt': robots_txt})

                        # Calculate loading time and extract hyperlinks
                        loading_time = calculate_loading_time(url)
                        indicators.update({'loading_time': loading_time})

                        hyperlinks = identify_hyperlinks(get_hyperlinks(code, main), main)
                        internal_links = hyperlinks["internal"]
                        indicators.update({'internal_links': internal_links})
                        external_links = hyperlinks["external"]
                        indicators.update({'external_links': external_links})

                        url_length = identify_url_length(url)
                        indicators.update({'url_length': url_length})

                        https = identify_https(url)
                        indicators.update({'https': https})

                        micros_list = identify_micros(code)
                        indicators.update({'micros': micros_list})
                        micros = len(micros_list)

                        sitemap = identify_sitemap(code)
                        indicators.update({'sitemap': sitemap})

                        og = identify_og(code)
                        indicators.update({'og': og})

                        viewport = identify_viewport(code)
                        indicators.update({'viewport': viewport})

                        wordpress = identify_wordpress(code)
                        indicators.update({'wordpress': wordpress})

                        canonical = identify_canonical(code)
                        indicators.update({'canonical': canonical})

                        nofollow = identify_nofollow(code)
                        indicators.update({'nofollow': nofollow})

                        h1 = identify_h1(code)
                        indicators.update({'h1': h1})

                        if query:
                            # Identify keywords in code and URL, and calculate keyword density
                            keywords_in_code = identify_keywords_in_source(code, query)
                            keywords_in_url = identify_keywords_in_url(url, query)
                            keyword_density = identify_keyword_density(code, query)
                        else:
                            keywords_in_code = -1
                            keywords_in_url = -1
                            keyword_density = -1

                        indicators.update({'keywords_in_code': keywords_in_code,
                                        'keywords_in_url': keywords_in_url,
                                        'keyword_density': keyword_density})

                        description = identify_description(code)
                        indicators.update({'description': description})

                        title = identify_title(code)
                        indicators.update({'title': title})

                        # Write indicators to the database
                        write_indicators_to_db(indicators, result_id)

                        # Determine classification result based on indicators
                        optimized = 0
                        probably_optimized = 0
                        probably_not_optimized = 0
                        classification_result = "uncertain"

                        if tools_seo > 0 or sources_customers > 0 or sources_news > 0 or sources_ads > 0 or micros > 0:
                            optimized = 1
                            classification_result = 'most_probably_optimized'

                        if optimized == 0 and (tools_analytics > 0 or sources_shops > 0 or sources_company > 0 or viewport == 1 or robots_txt == 1 or sitemap == 1 or nofollow > 0 or canonical > 0 or (loading_time < 3 and loading_time > 0)):
                            probably_optimized = 1
                            classification_result = 'probably_optimized'

                        if (title == 0 or description == 0 or loading_time > 30) and og == 0:
                            classification_result = 'probably_not_optimized'

                        if sources_not_optimized > 0:
                            classification_result = 'most_probably_not_optimized'

                    else:
                        classification_result = 'error'

                    # Update the classification result in the database
                    db.update_classification_result(classification_result, result_id, classifier_id)

                except Exception as e:
                    print("seo rule based error:\n")
                    print(str(e))
                    classification_result = 'error'
                    db.update_classification_result(classification_result, result_id, classifier_id)

    # Retrieve results for the given classifier_id and classify them
    results = db.get_results(classifier_id, study_id)
    print(classifier_id)
    print(len(results))
    classify_results(results)
