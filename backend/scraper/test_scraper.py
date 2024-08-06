"""
This script provides a basic test to verify the functionality of a scraper.

It is advisable to use this script to test scrapers before integrating them into RAT (Result Assessment Tool).
"""

from libs.lib_scraping import *

def test_scraper_results(query, limit, scraper, headless):
    """
    Test the scraper by running it and printing the results.

    Args:
        query (str): The search query to be used by the scraper.
        limit (int): The maximum number of results to retrieve.
        scraper (object): The scraper instance to use.
        headless (bool): Whether to run the scraper in headless mode.
    """
    # Execute the scraper and fetch results
    search_results = run(query, limit, scraper, headless)
    
    try:
        # Check if the scraper returned valid results
        if search_results != -1:
            # Print the results with an index
            for i, sr in enumerate(search_results, start=1):
                # Uncomment the following lines to print specific parts of each result
                # print(sr[0])  # Example: Print the first element of the search result
                # print(sr[1])  # Example: Print the second element of the search result
                print(f"Result {i}: {sr[2]}")  # Print the third element of the search result
        else:
            print("Scraping test failed: No results were returned.")
    except Exception as e:
        # Print any exception that occurs during the test
        print(f"An error occurred: {str(e)}")


# Define the query for testing
test_query = "test"  

# Example of how to use different scrapers:
# Uncomment and modify the following lines to test different scrapers

# from scrapers.bing_de import *
# se = Scraping()
# test_scraper_results(test_query, 10, se, True)

# from scrapers.bing_de import *
# se = Scraping()
# test_scraper_results(test_query, 10, se, True)

from scrapers.duckduckgo_de import *
se = Scraping()
test_scraper_results(test_query, 10, se, False)

# from scrapers.ecosia_de import *
# se = Scraping()
# test_scraper_results(test_query, 10, se, True)
