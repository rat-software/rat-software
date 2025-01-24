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
    Classify a webpage based on input data and return the classification result.

    Args:
        data: Dictionary containing 'url', 'main', 'code', and 'query' keys with corresponding values.

    Returns:
        str: Classification result indicating whether the webpage is about RAT or not.
    """

    # Extract data from the input dictionary
    url = data["url"]
    main = data["main"]
    code = data["code"].lower().split()
    query = data["query"].lower()

    # Generate indicators in a single operation
    indicators = {
        "query_counter": code.count(query),
        "url_counter": url.count(query),
        "main_counter": main.count(query)
    }

    # Classify the results based on indicators
    if indicators["query_counter"] > 5 and (indicators["url_counter"] > 0 or indicators["main_counter"] > 0):
        return "Webpage is about RAT"
    else:
        return "Webpage is not about RAT"

# Function to read file content
def read_file_content(filename):
    """
    Read and return the content of a file.

    Args:
        filename: The path to the file to read.

    Returns:
        str: Content of the file as a string.
    """

    with open(filename, encoding='utf-8', errors='ignore') as f:
        return f.read()

# Example usage
if __name__ == "__main__":
    data_examples = [
        {
            "url": "https://searchstudies.org/research/rat/",
            "main": "https://searchstudies.org/",
            "query": "rat",
            "code": read_file_content("example_for_classifier_01.html")
        },
        {
            "url": "https://www.haw-hamburg.de",
            "main": "https://www.haw-hamburg.de",
            "query": "rat",
            "code": read_file_content("example_for_classifier_02.html")
        }
    ]

    for data in data_examples:
        result = classify_result(data)
        print(result)
