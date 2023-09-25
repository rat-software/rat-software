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
