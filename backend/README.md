# Result Assessment Tool (RAT) backend application
- The backend application consists of of three sub applications which could be installed separately for a better resource management. However in most cases an installation of all apps on one server should be decent.

#### Applications in backend
- Classifier: toolkit to use and add classifiers based on the data RAT provides
- Scraper: library for scraping search engines
- Sources: library for scraping content of URLs

#### Configuration of the applications
All applications share the folder /config/ that consits of json files to change the database connection (config_db.ini), change proxy info (config_proxy.ini) and to change options for scraping of sources (config_sources.ini)

#### Run the backend application
- The backend applications are built on Appsheduler to make them running in the background. Starting all services at one can be executed by running **source start_rat_server.sh** or by using **nohup python backend_controller_start.py**
- Alternatively all applications offer their controllers, if it is needed to run them seperately on different machines.
