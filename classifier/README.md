# Classifier
The classifier can be used to configure classifiers for the sources. It is a flexible app where you can define your own classifiers using the database.

## Set up the app

- Change config_db.ini to connect the app to the rat database

## Set up the classifier

To  setup classifiers, you have to use and store information in the rat database. The classifier_db_lib provides functions to read search results and their contents for classification purposes.

Here is an overview of the tables used for classifiers:

- result: the result table stores the scrapped and imported urls. The tool reads all the information of a stored result to provide the data to the classifier.
- source: the source table stores the content of the search results or imported URLs. It provides the information as html source code and also as an image.
- classifierindicator: table to store the indicators for a classifier.
- classifierresult: table to store the result of a classification for a search result or an imported URL.

### Manually adding a classifier:
- Add a folder with the name of your classifier
- Add a python fileas module for your classifier
- Change the config_classifier.ini to add the classifier

```
{
	"your_classifier": { //name of the classifier
		"module": "your_classifier_module" //name of the module
	}
}
```

### Setting up the classifier module

- Every classifier module should start with:

```
from classifier_db_lib import *

classifier = "your_classifier"

def main():

    values = get_values(classifier)

    for value in values:

        result = value['id']

        insert_classification_result(classifier, "in process", result)
```


To use the classifier you need to set up a main function by using these database functions

- get_values(classifier) // read values for the classifier. You will get the following information to work with:

```
- id = id of search result
- url = url of search result
- main = main url of search result
- position = position on serp
- searchengine = name of search engine
- title = title on serp
- description = description on serp
- ip = ip of search result
- code = source code of search result
- bin = screenshot of search result
- final_url = redirected url of search result
```

- insert_classification_result(classifier, "in process", id) // function to insert the classification process, storing the current state

- update_classification_result(classifier, classification_result, id) // function to update the result of your classification process

## Run the app

The app is built on the python background process sheduler, as scraping web pages is time and performance consuming.

- To start the app
```
(sources) > nohup python classifier_start.py >classifier.out &
```

- To stop the app
```
(sources) > python classifier_stop.py
```

- Alternatively, you can simply configure cronjobs to run classifier.py
