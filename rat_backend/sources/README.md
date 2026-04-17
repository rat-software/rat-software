# RAT: Sources Scraper

The **Sources Scraper** is the data acquisition engine of the RAT platform. It is a Selenium-based worker designed to navigate to URLs, capture their full HTML source code, and take high-resolution screenshots. It operates as a background task, typically installed on dedicated servers to manage the resource-intensive nature of web scraping.

## 🚀 Features

* **Dual Capture**: Simultaneously retrieves the complete rendered HTML and a JPEG screenshot of any target URL.
* **Headless Operation**: Optimized for server environments using headless browser modes.
* **Storage Integration**: Automatically packages captured data into ZIP archives and uploads them to the centralized **RAT Storage Service**.
* **Automated Retries**: Includes a "reset" mechanism that identifies and re-queues failed or interrupted scraping jobs.
* **Concurrency Support**: Uses a multi-threaded scheduler to process multiple URLs simultaneously based on server capacity.

---

## 🛠 1. Installation & System Requirements

Scraping requires specific system-level dependencies to manage browser instances.

### System Dependencies (Linux)
```bash
sudo apt update
sudo apt install -y chromium-browser chromium-chromedriver psutil
```

### Setup
Transfer the source files to your server and set up a Python virtual environment:
```bash
python -m venv venv_rat_sources
source venv_rat_sources/bin/activate
```

### Install Dependencies
```bash
python -m pip install --no-cache-dir -r requirements.txt
```

---

## ⚙️ 2. Configuration

The scraper relies on two primary configuration files located in the `/config` directory:

* **`config_db.ini`**: Contains the connection parameters for the central PostgreSQL database.
* **`config_sources.ini`**: Defines application-specific settings, including:
    * `job_server`: A unique name for this scraper instance.
    * `wait_time` & `timeout`: Controls for page loading and process duration.
    * `storage_base_url` & `api_key`: Credentials for the Storage Service.

---

## 🗄 3. Database Interaction

The scraper interacts with the following core tables:

* **`result`**: Monitors this table for URLs that need to be scraped.
* **`result_source`**: Tracks the scraping progress and attempt counter for each result. It uses status codes: `0` (pending), `2` (processing), `1` (success), and `-1` (error).
* **`serp`**: If configured, the scraper can also capture screenshots of full Search Engine Result Pages.

---

## 🖥 4. Management & Operation

### Individual Operation
To run the scraper on a dedicated machine:
* **Start**: `nohup python sources_controller_start.py &`. This launches the scraping thread (`job_sources.py`) and the reset thread (`job_reset_sources.py`).
* **Stop**: `python sources_controller_stop.py`. This script is essential for cleaning up "zombie" browser processes (Chrome/Chromium) and resetting pending jobs in the database.

### Unified Backend Control
When running as part of the full RAT backend:
* **Start All**: `python backend_controller_start.py`.
* **Stop All**: `python backend_controller_stop.py`.

---

## 🧹 5. Reliability & Debugging

* **Job Resets**: The `sources_controller_start.py` automatically initiates a reset thread that moves failed jobs back into the queue if they exceed the defined `refresh_time`.
* **Logging**: All operations, errors, and runtimes are recorded in `sources.log` for detailed debugging.
* **Testing**: Use `test_sources_storage.py` to verify that the scraper can successfully capture a page and upload it to your Storage Service.

---

## 📜 License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007