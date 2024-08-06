# RAT

## Set up the Server Backend
- Make sure you installed Google Chrome on your System
- Copy all files from backend on your Server: https://www.google.com/intl/en/chrome/
- It is highly recommended to set up a backend in a virtual enviroment install the venv and activate it:
```
python -m venv venv_rat_backend
source venv_rat_backend/bin/activate
```

- Next install packages from the requirements.txt from the backend directory
```
python -m pip install --no-cache-dir -r requirements.txt
```

- Next initialize seleniumbase for the first time by the script XXXX to download the newest driver

source /home/rat-backend/rat/bin/activate
python.exe -m pip install --upgrade pip
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
pip install pdoc3
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

