'''
This is a template file that allows you to write your own classify_result function for your classifier based on data that RAT can provide. 

Scraping search engines with RAT makes it possible to create a classifier based on the following inputs:
- URL of a web page
- Main URL of the website
- Position in the search engine ranking
- Title from the search result snippet
- Description from the search result snippet
- IP address of the website
- Source code of the website
- Screenshot of the website
- Search query

In the template, however, we will only use the source code of a web document and a predefined search query, the URL and the main URL of the example.

When you are done with your own function to classify a result, you need to add it to: backend/classifier/classifiers/classifier_template.py and save the template as your new classifier.

To do this, you need to create a folder with the same name as your classifier.py file.

Then you need to add it to the "classifier" table in the database.
Add the name of your classifier (same name as the folder and Python file) and a display name for the user interface.
'''

def classify_result(data):
    """
    Main function for your classifier.

    Args:
        data (dict): The data for the classifier.

    Returns:
        None
    """

    url = data["url"]
    main = data["main"]
    code = data["code"].lower().split()
    query = data["query"].lower()

    indicators = {}

    # generate indicators. indicators should be stored dictionaries with a key with the name of the indicator and the value to store them in the database.

    query_counter = code.count(query)
    indicators = {"query_counter": query_counter}

    url_counter = url.count(query)
    indicators = {"url_counter": url_counter}

    main_counter = main.count(query)
    indicators = {"main_counter": main_counter}

    # classify the results

    classification_result = ""

    if query_counter > 5 and (url_counter > 0 or main_counter > 0):
        classification_result = "Webpage is about RAT"
    else:
        classification_result = "Webpage is not about RAT"

    print(classification_result)

# Create the data for the classifier

data = {
    "url": "https://searchstudies.org/research/rat/",
    "main": "https://searchstudies.org/",
    "query": "rat",
}

with open("example_for_classifier_01.html", encoding='utf-8', errors='ignore') as f:
    data["code"] = f.read()

classify_result(data)

data = {
    "url": "https://www.haw-hamburg.de",
    "main": "https://www.haw-hamburg.de",
    "query": "rat",
}

with open("example_for_classifier_02.html", encoding='utf-8', errors='ignore') as f:
    data["code"] = f.read()

classify_result(data)
