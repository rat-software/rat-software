# Classifier

The Classifier application allows you to configure and use classifiers for various data sources. It is a flexible tool that enables you to define and manage custom classifiers using a database.

## Setting Up the Application

1. **Configure Database Connection:**
   - Edit the configuration file located at **/backend/config/config_db.ini** to connect the application to the RAT database.

## Configuring the Classifier

To set up classifiers, use the RAT database to store and manage classification data. The `classifier_db_lib` provides functions to read and classify search results and their contents.

### Database Tables Overview

- **result**: Stores scraped and imported URLs. The tool retrieves information from this table to feed into the classifier.
- **source**: Contains the content of search results or imported URLs, including HTML source code and screenshots.
- **classifier_indicator**: Stores indicators used by the classifier.
- **classifier_result**: Stores the results of classifications for search results or imported URLs.

## Adding a New Classifier

1. **Create Classifier Files:**
   - Create a folder named after your classifier in the folder **/classifiers/**.
   - Add a Python file named after your classifier within this folder to serve as your classifier module.

2. **Update Database:**
   - Open the `classifier` table in your PostgreSQL database.
   - Add an entry for your classifier, including an internal name and a display name for the Flask frontend. Ensure that the folder name, Python file name, and database name match, as relative paths are used for initialization.

## Setting Up the Classifier Module

1. **Use the Template:**
   - Use **/classifiers/classifier_template/classifier_template.py** as a template for your classifier.

2. **Customize the Classifier:**
   - Locate the section marked: `'''Define your indicators and classification rules here'''`.
   - Modify the example provided to suit your needs.
   - For an example of a custom classifier function, please refer to **/classifiers/classifier_template/example_classify_result_function.py**.

3. **Available Data:**
   Your classifier can use the following data:
   ```
   - id = ID of the search result
   - url = URL of the search result
   - main = Main URL of the search result
   - position = Position in the search list
   - searchengine = Name of the search engine
   - title = Title of the search result
   - description = Description of the search result
   - ip = IP address associated with the search result
   - code = Source code of the search result
   - bin = Screenshot of the search result
   - final_url = Redirected URL of the search result
   ``` 

4. **Available Jupyter Notebooks**
   - To test your new classifier function, use the Jupyter Notebook template found at [/templates/new_classifier_function.ipynb](https://github.com/rat-software/rat-software/blob/main/templates/new_classifier_function.ipynb).
   - To add a new classifier to the database, refer to the Jupyter Notebook located at [/templates/add_classifier_to_database.ipynb](https://github.com/rat-software/rat-software/blob/main/templates/add_classifier_to_database.ipynb).

## Starting and Stopping the Classifier

- **To Start the Application:**
```bash
nohup python classifier_controller_start.py
```

- **To Stop the Application:**
```bash
python classifier_controller_stop.py
```

- **Alternative Method:**
You can configure cron jobs to run `classifier.py` and `classifier_reset.py` at scheduled intervals.

