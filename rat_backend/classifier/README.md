# RAT: Classifier Module

The Classifier is the analytical heart of the RAT backend. It processes the data captured by the Scraper (HTML and screenshots) to generate structured insights and indicators, such as SEO scores or content classifications.

## 🚀 Features

* **Modular Analysis**: Easily add new classification logic by creating a dedicated folder and script.
* **Database Integrated**: Automatically retrieves pending results and stores findings in dedicated indicator tables.
* **Automatic Recovery**: Includes a reset utility to handle jobs interrupted by server restarts or crashes.
* **SEO Scorer Included**: Comes pre-packaged with a comprehensive SEO scoring engine.

---

## 🛠 1. Installation & Setup

### Step 1: Prepare the Environment
Transfer the backend files to your server and set up a Python virtual environment:
```bash
python -m venv venv_rat_classifier
source venv_rat_backend/bin/activate
```

### Step 2: Install Dependencies
```bash
python -m pip install --no-cache-dir -r requirements.txt
```


### Configuration
* **Database**: Edit `backend/config/config_db.ini` to connect to your PostgreSQL instance.
* **Job Settings**: Edit `backend/config/config_sources.ini` to define your `job_server` name.

---

## 🗄 2. Database Structure

The Classifier interacts with several key tables to perform its duties:

* **`result`**: The source of imported or scraped URLs.
* **`source`**: Contains the raw HTML and screenshots retrieved by the scraper.
* **`classifier_indicator`**: Stores specific data points identified during analysis (e.g., meta tags, page load speed).
* **`classifier_result`**: Stores the final classification or score for a specific URL.

---

## 🧪 3. Adding a New Classifier

To expand the tool's capabilities, follow these steps to add a custom classifier:

1.  **Create Module**: Create a new folder in `/classifiers/` named after your tool (e.g., `my_analyzer/`).
2.  **Add Script**: Inside that folder, create `my_analyzer.py`. This script must contain a `main(classifier_id, db, helper, job_server, study_id)` function.
3.  **Register in DB**: Add an entry to the `classifier` table in your PostgreSQL database with the internal name matching your folder name.
4.  **Template**: Refer to `seo_score.py` for a detailed example of how to extract data and save indicators.

---

## ⚙️ 4. Management & Operation

### Standing on Its Own
If you prefer to run the Classifier independently of the other backend modules:
* **Start**: `nohup python classifier_controller_start.py &`.
* **Stop**: `python classifier_controller_stop.py`.

### Unified Backend Control
When using the master controller from the backend root directory:
* **Start All**: `python backend_controller_start.py` (This launches the Classifier in its own thread).
* **Stop & Reset**: `python backend_controller_stop.py` (Terminates the classifier and resets stuck jobs).

---

## 🧹 5. Troubleshooting & Resets

If analysis jobs appear "stuck" in the database:
1.  The `classifier_controller_start.py` automatically launches `classifier_reset.py` in the background.
2.  This reset script identifies jobs marked as "in progress" that haven't been updated recently and returns them to the queue for a fresh attempt.

---

## 📜 License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007