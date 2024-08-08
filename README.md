# RAT

The Result Assessment Tool (RAT) is a software toolkit that allows researchers to conduct large-scale studies based on results from (commercial) search engines and other information retrieval systems. It is developed by the research group Search Studies at the Hamburg University of Applied Sciences in Germany. The RAT project is funded by the German Research Foundation.

## RAT Extensions
The repository provides an overview of extensions created by our developer community: https://github.com/rat-extensions

## RAT Project resources
- For detailed information about the research project and additional resources, visit: https://searchstudies.org/research/rat-software/
- Information about how to contribute: https://searchstudies.org/rat-how-to-contribute/
- An installation of RAT can be accessed at: https://rat-software.org/
- Datasets generated using RAT and supplementary documentation can be found at: https://osf.io/t3hg9/
- Videos from the RAT Community Meeting are available at: https://www.youtube.com/watch?v=K2Gev8C7Xxw&list=PLiTHQpIQWsZwRaDAgFTANPvI3fHMncXUO

## Contributors to RAT
- #### Project Lead: [Professor Dirk Lewandowski](https://searchstudies.org/team/dirk-lewandowski/) - https://github.com/dirklew
- #### Lead Software Engineer and Developer: [Sebastian Sünkler](https://searchstudies.org/team/sebastian-suenkler/) - https://github.com/sebsuenkler
- #### Current Frontend Developer and Assistant: [Tuhina Kumar](https://searchstudies.org/team/tuhina-kumar/) - https://github.com/tuhinak
- #### Former Frontend Developer: Nurce Yagci - https://github.com/yagci
- #### Usability and User Experience Specialist: [Sebastian Schultheiß](https://searchstudies.org/team/schultheiss/)
- #### Student Assistant for Software Engineering: [Sophia Bosnak](https://searchstudies.org/team/sophia-bosnak/) - https://github.com/kyuja
- #### Current and former students from the University of Duisburg-Essen have developed extensions for RAT as part of their theses: https://github.com/rat-extensions
   - https://github.com/MnM3
   - https://github.com/mohamedsaeed21
   - https://github.com/g1thub-4cc0unt
   - https://github.com/Samustafa

## Publications related to the project
- Sünkler S.; Yagci, N.; Schultheiß, S.; von Mach, S.; Lewandowski, D.; (2024) Result Assessment Tool Software to Support Studies Based on Data from Search Engines In: Part of the book series: Lecture Notes in Computer Science https://link.springer.com/chapter/10.1007/978-3-031-56069-9_19
- Sünkler, S.; Yagci, N.; Sygulla, D.; von Mach, S.; Schultheiß, S., Lewandowski, D.; (2023). Result Assessment Tool (RAT): A Software Toolkit for Conducting Studies Based on Search Results. In: Proceedings of the Association for Information Science and Technology https://doi.org/10.1002/pra2.972
- Schultheiß, S.; Lewandowski, D.; von Mach, S.; Yagci, N. (2023). Query sampler: generating query sets for analyzing search engines using keyword research tools. In: PeerJ Computer Science 9(e1421). http://doi.org/10.7717/peerj-cs.1421
- Schultheiß, S.; Sünkler, S.; Yagci, N.; Sygulla, D.; von Mach, S.; Lewandowski, D.; (2023). Simplify your Search Engine Research : wie das Result Assessment Tool (RAT) Studien auf der Basis von Suchergebnissen unterstützt. In: Proceedings des 17. Internationalen Symposiums für Informationswissenschaft (ISI 2023), 429-437. https://zenodo.org/records/10009338
- Sünkler, S.; Yagci, N.; Sygulla, D.; von Mach, S.; Schultheiß, S.; Lewandowski, D.; (2023). Result Assessment Tool (RAT): Software-Toolkit für die Durchführung von Studien auf der Grundlage von Suchergebnissen. In: Proceedings des 17. Internationalen Symposiums für Informationswissenschaft (ISI 2023), 438-444. https://zenodo.org/records/10009338
- Sünkler, S., Yagci, N., Sygulla, D., von Mach, S., Schultheiß, S. Lewandowski, D. (2022). Result Assessment Tool (RAT). Informationswissenschaft im Wandel. Wissenschaftliche Tagung 2022 (IWWT22), Düsseldorf. https://zenodo.org/records/7092079

# Installation of RAT

The source code consists of three individual applications:

1. Web Interface (frontend)
2. Server backend (backend)
3. Google Query Sampler (optional)

RAT runs on Python and has a PostgreSQL database, the web interface is a Flask app. You can install both applications on one server or split the applications to share the workload, e. g. having 2 backends for scraping on one server and the flask app on another one.

To set up your own version of RAT, you need to clone the repository and follow these steps:

## Set up the database for all applications
- Download and install [PostgreSQL](https://www.postgresql.org/download/)
- Import database
```
(rat-demo) > createdb -T template0 dbname
(rat-demo) > psql dbname < install_database/rat-db-install.sql
```

## Install Python
- Install [Python](https://www.python.org/downloads/)

## Installation of dependencies for both applications on one server:
- Install Python packages from the `requirements.txt` in the root folder:
```
python -m pip install --no-cache-dir -r requirements.txt
```


## Set up the web interface (Flask Application / Frontend)
#### Access the documentation for the frontend at: https://searchstudies.org/rat-frontend-documentation/

- Create a virtual environment

```bash
python -m venv venv_rat_frontend
source venv_rat_frontend/bin/activate
```

- Install Python packages from the `/frontend/requirements.txt`
```
python -m pip install --no-cache-dir -r requirements.txt
```
- Add own data to config file `config.py`

| Setting | Example |
| ---- | ---- |
| SQLALCHEMY_DATABASE_URI | 'postgresql://USERNAME:PASSWORD@SERVER/DBNAME' |
| SECRET_KEY | [How to generate](https://flask-security-too.readthedocs.io/en/stable/quickstart.html#sqlalchemy-application) |
| SECURITY_PASSWORD_SALT | [How to generate](https://flask-security-too.readthedocs.io/en/stable/quickstart.html#sqlalchemy-application) |
| MAIL_SERVER | server.domain.de |
| MAIL_USERNAME | name@mail.de |
| MAIL_PASSWORD | password |

* Google Mail does no longer allow 3rd party apps to send mails, if there is no other mail adress you can use [Mailtrap](https://mailtrap.io/)
- Start Flask
```
export FLASK_APP=rat.py
flask run
```

# Result Assessment Tool (RAT) Backend application.
#### Access the documentation for the backend at: https://searchstudies.org/rat-backend-documentation/

## Setting Up the Server Backend

1. **Install Google Chrome**  
   Ensure that Google Chrome is installed on your system. You can download it from [here](https://www.google.com/intl/en/chrome/).

2. **Copy Backend Files**  
   Transfer all files from the `backend` directory to your server.

3. **Set Up a Virtual Environment**  
   It is highly recommended to set up the backend in a virtual environment. Install `venv` and activate it with the following commands:
    ```bash
    python -m venv venv_rat_backend
    source venv_rat_backend/bin/activate
    ```

4. **Install Dependencies**
   Install the required packages from the requirements.txt file located in the backend directory:
    ```bash
    python -m pip install --no-cache-dir -r requirements.txt
    ```

5. **Initialize SeleniumBase**
Run the script initialize_seleniumbase.py to download the latest WebDriver:
    ```bash
    python initialize_seleniumbase.py
    ```


The RAT backend application consists of three sub-applications, which can be installed separately for better resource management. However, installing all sub-applications on one server is generally recommended.

## Backend Applications
- classifier: A toolkit for using and adding classifiers based on data provided by RAT.
- scraper: A library for scraping search engines.
- sources: A library for scraping content from URLs.

## Configuration
All applications share the /config/ folder, which contains JSON files for configuring:
- Database Connection: `config_db.ini`
- Scraping Options: `config_sources.ini`

## Running the Backend Application
- The backend applications use `appsheduler` to run in the background. To start all services simultaneously, use:
    ```bash
    nohup python backend_controller_start.py &
    ```
- Alternatively, each application has its own controller if you prefer to run them separately on different machines.

# Result Assessment Tool (RAT) Google Query Sampler.
#### Access the documentation for the query sampler at: https://searchstudies.org/rat-query-sampler-documentation/


## Introduction

The Query Sampler App is a Flask-based web application that generates keyword ideas using the Google Ads API. The application requires API access to Google Ads Services to function correctly.

For detailed instructions on setting up and using the Google Ads API, visit the [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start?hl=en). You will need to create an account and apply for a developer token to use the API. For Python implementation, refer to [Daniel Heredia Mejias' guide](https://www.danielherediamejias.com/python-keyword-planner-google-ads-api/).

## Dependencies

To install the necessary dependencies, run:

```bash
pip install flask
pip install flask_simplelogin
pip install python-dotenv
pip install pandas
pip install google-ads
pip install psycopg2
```

## Folder Structure and Important Files
- `app/`: Contains the Flask application.

- `static/`: Static files for the application.
- `templates/`: Templates used to render the app.
- `keywords/`: Templates for managing keyword sets and forms for language and region selection.
- `studies/`: Templates for creating and viewing studies. Templates for editing studies are also included.
- `base.html`: Base template, index, static legal site, and login template (for Flask-SimpleLogin).
- `db.py`: Library for all database operations. Change the database connection information here.
- `forms.py`: Contains form classes used in the app.
- `routes.py`: Flask router with all route handlers.
- `google_ads/`: Contains scripts for generating keyword ideas using the Google Ads API.

- `generate_user_credentials.py`:
1. Run `python generate_user_credentials.py --client_secrets_path=client.json` to create a new refresh token.
2. Open the provided URL in your terminal.
3. Log in with your Google-Ads credentials
4. Replace the refresh token in the `google-ads.yaml` file.

- `generate_keywords.py`: Script for generating keyword ideas. This script imports db.py to read from and write to the database and cannot be used standalone.
- `generate_keywords_demo.py`: Standalone script to test API access.
- `install/`: Contains CSV files and a script to insert official language and region codes provided by Google (necessary only for setting up a new database).
- `.flaskenv`: Contains environment parameters for the Flask app.

## Running the App
To test the app locally, use the built-in Flask server. Run the following command from the root folder:

```bash
flask run --host=0.0.0.0
```
