# RAT
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

# Result Assessment Tool (RAT) Backend application.

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
- The backend applications use `apsheduler` to run in the background. To start all services simultaneously, use:
    ```bash
    nohup python backend_controller_start.py &
    ```
- Alternatively, each application has its own controller if you prefer to run them separately on different machines.

