# Classifier
The classifier can be used to configure classifiers for the sources. It is a flexible app where you can define your own classifiers using the database.

## Set up the app

- Change /backend/config/config_db.ini/config_db.ini to connect the app to the rat database

## Set up the classifier

To  setup classifiers, you have to use and store information in the rat database. The classifier_db_lib provides functions to read search results and their contents for classification purposes.

Here is an overview of the tables used for classifiers:

- result: the result table stores the scrapped and imported urls. The tool reads all the information of a stored result to provide the data to the classifier.
- source: the source table stores the content of the search results or imported URLs. It provides the information as html source code and also as an image.
- classifier_indicator: table to store the indicators for a classifier.
- classifier_result: table to store the result of a classification for a search result or an imported URL.

### Manually adding a classifier:
- Add a folder with the name of your classifier
- Add a python file as module for your classifier
- Open the table classifier in your PostgreSQL database and add the classifier name (internal name of the classifier) and a display name for the Flask frontend, It is important that the name of the folder, the python file and the name in the database match because of using relative paths to initialize the classifier

### Setting up the classifier module

- Use the file /classifiers/classifier_template/classifier_template.py as a template to add your own classifiers.
- Search for the block starting with: '''Define your indicators and classification rules here'''
- Change the simple example to your needs.
- You can work with the following data for your classifier:
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

## Run the classifier

The app is built on the python background process sheduler, as scraping web pages is time and performance consuming.

- To start the app
```
(sources) > nohup python classifier_controller_start >classifier.out &
```

- To stop the app
```
(sources) > python classifier_controller_stop.py
```

- Alternatively, you can simply configure cronjobs to run classifier.py
