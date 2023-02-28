# RAT Demo

The Result Assessment Tool (RAT) is a software toolkit that allows researchers to conduct large-scale studies based on results from (commercial) search engines and other information retrieval systems. It is developed by the research group Search Studies at the Hamburg University of Applied Sciences in Germany. The RAT project is funded by the German Research Foundation.

The source code consists of four individual modules:

1. Database (database)
2. Web Interface (tool)
3. Results Scraper (results)
4. Sources Scraper (sources)
5. Classifier (classifier)

RAT runs on Python and has a PostgreSQL database, the web interface is a Flask app.
To set up your own version of RAT, you need to clone the repository and follow these steps:

## Set up the database
- Download and install [PostgreSQL](https://www.postgresql.org/download/)
- Import database
```
(rat-demo) > createdb -T template0 dbname
(rat-demo) > psql dbname < database/db_create.sql
(rat-demo) > psql dbname < database/db_insert.sql
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

## Set up the results scraper

- Installation of Firefox/geckodriver and selenium
```
pip install -U selenium==4.1.0
wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz
tar -x geckodriver -zf geckodriver-v0.30.0-linux64.tar.gz -O > /usr/local/bin/geckodriver
chmod +x /usr/local/bin/geckodriver
rm geckodriver-v0.30.0-linux64.tar.gz
```

## Set up the sources scraper

- Install Python packages from the folder sources
```
(venv) > pip install -r requirements.txt
```

- Change config_db.ini in the sources folder with the data of the common RAT database

## Set up the classifier

- Install Python packages from the folder classifier
```
(venv) > pip install -r requirements.txt
```

- Change config_db.ini in the classifier folder with the data of the common RAT database
