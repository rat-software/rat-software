# ⚙️ RAT: Backend Installation & Management

The **RAT Backend** is a multi-service engine responsible for data acquisition and analysis. It consists of three primary modules managed by a **Unified Backend Controller**, allowing you to start and stop the entire ecosystem with single commands.

## 🏗️ Backend Architecture

| Module | Role | Key Technology |
| :--- | :--- | :--- |
| **Sources Scraper** | Web content and screenshot capture. | Selenium / Chromium |
| **Query Sampler** | Google Ads API keyword discovery. | Google Ads python3 Client |
| **Classifier** | Data analysis and SEO scoring. | BeautifulSoup / SQL |
| **Unified Controller** | Master management and process cleanup. | python3 Threading / psutil |

---

## 🛠️ 0. Prerequisites

Before installing the backend, ensure your server has the following:
* **python3 3.12**
* **Google Chrome / Chromium**: Required for the Sources Scraper.
* **PostgreSQL**: The central database where all results are stored[cite: 1].

---

## 🚀 1. Installation Steps

### Step 1: Prepare the Environment
Transfer the backend files to your server and set up a python3 virtual environment:
```bash
python3 -m venv venv_rat_backend
source venv_rat_backend/bin/activate
```

### Step 2: Install Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements_rat_backend.txt
```

### Step 3: Module-Specific System Setup
* **Sources Scraper**: Ensure `chromium-chromedriver` is installed on your system path.
* **Query Sampler**: You must generate your refresh token before the first run:
    ```bash
    python3 query_sampler/generate_user_credentials.py --client_secrets_path=client.json
    ```

---

## ⚙️ 2. Configuration

All backend components share a central `/config` directory. Update these templates with your credentials:

1.  **`config_db.ini`**: Set your PostgreSQL connection details.
2.  **`config_sources.ini`**: Define your `job_server` name, storage API key, and scraping timeouts.
3.  **`google-ads.yaml`**: Update with your developer token and OAuth2 credentials in the `query_sampler/` folder.

---

## 🖥️ 3. Deployment & Operation

The backend uses a two-tier approach to reliability: **Individual Resets** for runtime errors and **Controller Stops** for service termination.

### Individual Job Resets (Automatic)
You do **not** need to stop the service to fix stuck jobs. The Scraper and Classifier modules run dedicated "reset" threads alongside the main workers.
* These threads automatically re-queue jobs that are stuck in "progress" without killing other active processes.

### Production: Running as a System Service
When deploying via `systemd`, the `ExecStop` should only be used for intentional maintenance or full service shutdowns.

**Service File Location**: `/etc/systemd/system/rat-backend.service`
```ini
[Unit]
Description=RAT Unified Backend Controller
After=network.target postgresql.service

[Service]
User=your_username
Group=www-data
WorkingDirectory=/path/to/rat/backend
Environment="PATH=/path/to/rat/backend/venv_rat_backend/bin"

# Launches Scraper, Classifier, and Query Sampler threads
ExecStart=/path/to/rat/rat-backend/venv_rat_backend/bin/python3 backend_controller_start.py

# ONLY for full service termination. 
# This kills all browsers and wipes pending jobs from the DB for this server.
ExecStop=/path/to/rat/rat/venv_rat_backend/bin/python3 backend_controller_stop.py

# Use a conservative restart to avoid frequent DB resets during crash loops
Restart=on-failure
RestartSec=30 

[Install]
WantedBy=multi-user.target
```

---

## 🧹 4. Maintenance Notes
* **Full Stop (The "Nuclear" Option)**: Running `backend_controller_stop.py` is a heavy operation. It kills all `chromium`, `chrome`, and `uc_driver` processes and deletes "in-progress" entries from the `result_source` table for the current `job_server`.
* **Zombie Processes**: If server RAM usage is unexpectedly high and the service is **stopped**, run the stop controller manually to ensure no detached browser instances remain.
* **Safety Buffer**: The stop script includes a 60-second wait period to ensure browser processes have fully exited before the final database cleanup occurs.

---

## 📜 License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007