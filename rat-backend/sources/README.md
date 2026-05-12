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
# For Ubuntu 20.04 and earlier:
sudo apt install -y chromium-browser chromium-chromedriver psutil

# For Ubuntu 22.04 and later (chromium is a snap package):
sudo apt install -y chromium-chromedriver psutil
sudo snap install chromium

# Note: On some distributions, you may need to install `chromium` or `google-chrome` instead of `chromium-browser`.
```

### Setup
Transfer the source files to your server and set up a Python virtual environment:
```bash
python3 -m venv venv_rat_sources
source venv_rat_sources/bin/activate
```

### Install Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements_rat_sources.txt
```

---

## ⚙️ 2. Configuration

The scraper relies on two primary configuration files located in the `/config` directory:

* **`config_db.ini`**: Contains the connection parameters for the central PostgreSQL database.
* **`config_sources.ini`**: Defines application-specific settings, including:
    * `job_server`: A unique name for this scraper instance.
    * `wait_time` & `timeout`: Controls for page loading and process duration.
    * `storage_base_url` & `api_key`: Credentials for the Storage Service.

* **`result_source`**: Tracks the scraping progress and attempt counter for each result. Status codes are:
    * `0` (pending): The job is waiting to be processed.
    * `2` (processing): The job is currently being processed by a worker.
    * `1` (success): The job completed successfully.
    * `-1` (error): The job failed due to an error.

## 🗄 3. Database Interaction

The scraper interacts with the following core tables:

* **`result`**: Monitors this table for URLs that need to be scraped.
* **`result_source`**: Tracks the scraping progress and attempt counter for each result. It uses status codes: `0` (pending), `2` (processing), `1` (success), and `-1` (error).
* **`serp`**: If configured, the scraper can also capture screenshots of full Search Engine Result Pages.

---

## 🖥 4. Getting the Sources Scraper ready for Production

It is essential that the test scripts in the folder run successfully before you deploy the Sources Scraper on a production server.

* **`test_sources.py`**: Script to setup the Chrome instance and to check if the Sources Scraper is ready to go.
* **`test_sources_storage.py`**: Script to test the setup of the Sources Scraper and the connection to the rat-storage.

```bash
python3 test_sources.py
python3 test_sources_storage.py
```

* **Start**: `nohup python sources_controller_start.py > sources.log 2>&1 &`. This launches the scraping thread (`job_sources.py`) and the reset thread (`job_reset_sources.py`), redirecting all output to `sources.log` for easier log management.

### Individual Operation
To run the scraper on a dedicated machine:
* **Start**: `nohup python sources_controller_start.py &`. This launches the scraping thread (`job_sources.py`) and the reset thread (`job_reset_sources.py`).
* **Stop**: `python sources_controller_stop.py`. This script is essential for cleaning up "zombie" browser processes (Chrome/Chromium) and resetting pending jobs in the database.

### Unified Backend Control
When running as part of the full RAT backend:
* **Start All**: `python backend_controller_start.py`.
* **Stop All**: `python backend_controller_stop.py`.

---

## 🧹 6. Reliability & Debugging

* **Job Resets**: The `sources_controller_start.py` automatically initiates a reset thread that moves failed jobs back into the queue if they exceed the defined `refresh_time`.
* **Logging**: All operations, errors, and runtimes are recorded in `sources.log` (by default, created in the root directory of the scraper) for detailed debugging.
* **Testing**: Use `test_sources_storage.py` to verify that the scraper can successfully capture a page and upload it to your Storage Service.

---

## 📜 License
This project is licensed under the GNU General Public License Version 3 (GPLv3), June 29, 2007.
You are free to use, modify, and distribute this software under the terms of the GPLv3, which requires that derivative works and copies remain open source and include the same license.
For more details, see the full license text at: https://www.gnu.org/licenses/gpl-3.0.html