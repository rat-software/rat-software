# RAT

The Result Assessment Tool (RAT) is a software toolkit that allows researchers to conduct large-scale studies based on results from (commercial) search engines and other information retrieval systems. It is developed by the research group Search Studies at the Hamburg University of Applied Sciences in Germany. The RAT project is funded by the German Research Foundation (DFG –Deutsche Forschungsgemeinschaft) from 8/2021 until 10/2024, project number 460676551.

## RAT Extensions
The repository provides an overview of extensions created by our developer community: https://github.com/rat-extensions
- **Imprint Crawler**: A web crawler that is able to automatically extract legal notice information from websites while taking German legal aspects into account: https://github.com/rat-software/imprint-crawler. Developed by Marius Messer - https://github.com/MnM3
- **Readability Score**: A Python tool that extracts the main text content of a web document and analyzes its readability: https://github.com/rat-software/readability-score. Developey by Mohamed Elnaggar - https://github.com/mohamedsaeed21
- **Forum Scraper**: An extension to extract comments from German online news services: https://github.com/rat-software/forum-scraper. Developed by Paul Kirch - https://github.com/g1thub-4cc0unt
- **EI_Logger_BA**: A browser extension for conducting interactive information retrieval studies. With this extension, study participants can work on search tasks with search engines of their choice and both the search queries and the clicks on search results are saved: https://github.com/rat-software/EI_Logger_BA. Developed by Hossam Al Mustafa - https://github.com/Samustafa

# Installation of RAT

The source code consists of three individual applications:

1. Web Interface (frontend)
2. Server backend (backend)

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
