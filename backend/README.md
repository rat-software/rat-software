# RAT

The Result Assessment Tool (RAT) is a software toolkit that allows researchers to conduct large-scale studies based on results from (commercial) search engines and other information retrieval systems. It is developed by the research group Search Studies at the Hamburg University of Applied Sciences in Germany. The RAT project is funded by the German Research Foundation.

The source code consists of two individual applications:

1. Server backend (backend)
2. Web Interface (tool)

RAT runs on Python and has a PostgreSQL database, the web interface is a Flask app.
To set up your own version of RAT, you need to clone the repository and follow these steps:

## Set up the database
- Download and install [PostgreSQL](https://www.postgresql.org/download/)
- Import database
```
(rat-demo) > createdb -T template0 dbname
(rat-demo) > psql dbname < install_database/db_create.sql
(rat-demo) > psql dbname < install_database/db_insert.sql
```

## Set up the web interface
- Install [Python](https://www.python.org/downloads/)
- Create a virtual environment
```
(rat-demo) > cd tool
(tool) > python -m venv venv
(tool) > source venv/bin/activate
```
- Install Python packages
```
(venv) > pip install -r requirements.txt
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
(venv) > export FLASK_APP=rat.py
(venv) > flask run
```

## Set up the Server Backend

- Copy all files from backend on Linux Server
- It is highly recommended to set up a backend in a virtual enviroment:
```
apt-get install python3-venv
python3 -m venv rat
```
- If you work on a Debian server, you can just run the script to install all 
```
bash install-backend.sh
```
If your server runs on another OS, you have to follow these instructions to install all necessary packages and software:
- Install the current version of Chrome on your system (e. g. from https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb)
```
source /home/rat-backend/rat/bin/activate
pip install --upgrade pip
pip install pip-review
pip-review --local --auto
pip install wheel
pip install setuptools
pip install psutil
pip install apscheduler
pip install pandas
pip install beautifulsoup4
pip install lxml
pip install -U selenium
pip install psycopg2-binary
pip install -U pytest
pip install pdoc
pip install ipinfo
pip install pytest
pip install selenium-wire
pip install Pillow
pip install seleniumbase
pip install undetected-chromedriver
```
- Test, if the installation was successful (automatic testing is work in progress).
- Open folder /tests/
```
python test_db.py
python test_selenium.py
```

# Result Assessment Tool (RAT) Backend application.
- The backend application consists of three sub-applications that can be installed separately for better resource management. However, in most cases, it should make sense to install all applications on one server.

## Applications in the backend
- **classifier**: Toolkit for using and adding classifiers based on data provided by RAT.
- **scraper**: Library for scraping search engines
- **sources**: Library for scraping URL content

## Configuration of applications
All applications share the /config/ folder, which contains json files for changing the database connection **config_db.ini**, changing the proxy information **config_proxy.ini**, and changing the options for scraping sources **config_sources.ini**

## Running the backend application
- The backend applications are built on appsheduler to run in the background. Starting all services at once can be done by **source start_rat_server.sh** or by **nohup python backend_controller_start.py**.
- Alternatively, all applications provide their own controllers if you want to run them separately on different machines.

## Additional directories
- **crx**: Location of the browser extension **I don't care about cookies**: https://www.i-dont-care-about-cookies.eu/ This extension is needed because cookie banners can be a problem when scraping web pages
- **tests**: folder with tests using pytest (work in progress).
- **tmp**: temporary folder with screenshots of scraping processes

## Additional scripts
- **update_chrome_driver.py**: Script to update the current chrome driver on a Debian server (may not work properly on other machines).

