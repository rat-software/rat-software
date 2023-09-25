# Classifier
The classifier can be used to configure classifiers for the sources. It is a flexible application where you can define your own classifiers using the database.

## Setting up the application

- Change **/backend/config/config_db.ini/config_db.ini** to connect the app to the rat database

## Setting up the classifier

To set up classifiers, you need to use and store information in the rat database. The classifier_db_lib provides functions to read search results and their contents for classification purposes.

Here is an overview of the tables used for classifiers:

- **result**: The result table stores the scrapped and imported urls. The tool reads all the information of a stored result to provide the data to the classifier.
- **source**: The source table stores the content of the search results or imported URLs. It provides the information as html source code and also as an image.
- **classifier_indicator**: Table to store the indicators for a classifier.
- **classifier_result**: Table to store the result of a classification for a search result or an imported URL.

## Manually add a classifier:
- Add a folder with the name of your classifier
- Add a Python file as a module for your classifier
- Open the classifier table in your PostgreSQL database and add the classifier name (internal classifier name) and a display name for the Flask frontend. It is important that the name of the folder, the Python file and the name in the database match, as relative paths are used to initialize the classifier

## Setting up the classifier module

- Use the **/classifiers/classifier_template/classifier_template.py** file as a template to add your own classifiers.
- Look for the block that starts with: '''Define your indicators and classification rules here'''.
- Customize the simple example to fit your needs.
- You can work with the following data for your classifier:
```
- id = id of the search result
- url = url of the search result
- main = main url of the search result
- position = position on the search list
- searchengine = name of the search engine
- title = title of the search engine
- description = description on the search engine
- ip = ip of the search result
- code = source code of the search result
- bin = screenshot of the search result
- final_url = redirected url of the search result
```

## Start the classifier

The application is based on the Python background process Sheduler, as scraping web pages is time and performance consuming.

- To start the application
```
nohup python classifier_controller_start >classifier.out &
```

- To stop the application
```
python classifier_controller_stop.py
```

- Alternatively, you can simply configure cronjobs to run classifier.py
