# Sources Scraper

**Sources Scraper** is an application designed to capture and save the content of URLs as both text and screenshots. It operates as a background task and is intended to be installed on separate servers, independent of the main software. The app connects to the RAT via a PostgreSQL database.

## Setup

1. **Configure the Database Connection:**
   - Edit the `config_db.ini` file to configure the connection to the RAT database.

2. **Configure Application Settings:**
   - Edit the `config_sources.ini` file according to your requirements. Here, you can set various parameters such as `wait_time`, `timeout`, and `headless` mode.

## Running the Application

The application uses a Python background process scheduler due to the resource-intensive nature of web scraping.

- **To start the application:**

 - To start the application
```bash
nohup python sources_controller_start.py
```

- To stop the application
```bash
python sources_controller_stop.py
```

- Alternatively, you can set up cron jobs to schedule the execution of  **sources_scraper.py** and **sources_reset.py**.

## Debugging

The application includes a logging library that records progress and errors in sources.log for debugging purposes.
