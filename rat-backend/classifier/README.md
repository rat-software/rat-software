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
python -m pip install --upgrade pip
python -m pip install -r requirements_rat_classifier.txt
```

### Configuration
* **Database**: Edit `rat-backend/config/config_db.ini` to connect to your PostgreSQL instance.
* **Job Settings**: Edit `rat-backend/config/config_sources.ini` to define your `job_server` name.

---

## 🗄 2. Database Structure

The Classifier interacts with several key tables to perform its duties:

* **`result`**: The source of imported or scraped URLs.
* **`source`**: Contains the raw HTML and screenshots retrieved by the scraper.
* **`classifier_indicator`**: Stores specific data points identified during analysis (e.g., meta tags, page load speed).
* **`classifier_result`**: Stores the final classification or score for a specific URL.

---

## 🧪 3. Adding a Custom Classifier

RAT uses dynamic importing to execute your code. The easiest way to build a new classifier is to use the provided template files.

### 3.1. The Template Folder (Your Starting Point)
Before writing any code from scratch, look inside the `classifiers/classifier_template/` folder. It contains everything you need to get started:
*   **`classifier_template.py`**: The base boilerplate script.
*   **`example_classify_result_function.py`**: A working example showing how to check if a website is about RAT or not.

### 3.2. Architecture & Folder Structure
For RAT to recognize your classifier, the folder name and the main Python file must have the exact same name[cite: 13, 14]. 

To create a new tool called `my_analyzer`:
1. Create a new folder in `/classifiers/` named `my_analyzer/`.
2. Copy `classifier_template.py` into this new folder.
3. Rename the copied file to `my_analyzer.py`.

Your structure should look like this:
```text
rat-backend/
└── classifiers/
    └── my_analyzer/
        └── my_analyzer.py 
```

### 3.3. The Input Data & Decoding
When your classifier picks up a job, it pulls pending results from the database. Each result is passed as a dictionary containing everything the scraper found (`url`, `query`, `status_code`, etc.).

**⚠️ Decoding Required:** The `code` (HTML) and `picture` (Screenshot) are encoded in the database. You must decode them using the provided `helper` object:
```python
html_source = helper.decode_code(data["code"]) # Returns readable HTML string
screenshot = helper.decode_picture(data["bin"]) # Returns binary image data
```

### 3.4. Writing the Core Logic
A RAT classifier outputs two distinct types of data to the database: Indicators (`classifier_indicator`) and a Final Result (`classifier_result`).

Here is an example of core analysis logic separated from database operations:
```python
def analyze_page(data, helper):
    url = data["url"]
    query = data["query"].lower()
    html_code = helper.decode_code(data["code"])
    
    if data["status_code"] != 200 or not html_code:
        return "error", {}

    html_lower = html_code.lower()
    query_mentions = html_lower.count(query)
    
    indicators = {
        "Query Mentions": query_mentions,
        "URL Length": len(url)
    }
    
    final_result = "Highly Relevant" if query_mentions > 5 else "Not Relevant"
        
    return final_result, indicators
```

### 3.5. Local Testing (Sandbox Mode)
Before hooking your classifier up to the PostgreSQL database and the `main()` orchestrator, test your logic locally using the built-in sandbox. The template provides an `if __name__ == "__main__":` block to run the file directly from your terminal with mock data.

```python
# Example usage for local testing
if __name__ == "__main__":
    data_examples = [
        {
            "url": "https://searchstudies.org/research/rat/",
            "main": "https://searchstudies.org/",
            "query": "rat",
            "code": read_file_content("example_for_classifier_01.html") # Local mock HTML provided in the template
        }
    ]

    for data in data_examples:
        # Run your custom function against the mock data
        result, indicators = analyze_page(data, mock_helper) 
        print(f"Result: {result}")
        print(f"Indicators: {indicators}")
```

### 3.6. The Orchestrator: The `main()` Function
RAT expects your script to have a `main(classifier_id, db, helper, job_server, study_id)` function[cite: 14, 15]. This acts as the bridge between your logic and the PostgreSQL database to handle locking, duplicate checking, and saving.

```python
def main(classifier_id, db, helper, job_server, study_id):
    # Fetch pending results from the database
    results = db.get_results(classifier_id, study_id)
    
    # Lock the results immediately to prevent race conditions
    for result in results:
        result_id = result['id']
        if not db.check_classification_result(classifier_id, result_id):
            db.insert_classification_result(classifier_id, "in process", result_id, job_server)

    # Process each result
    for result in results:
        result_id = result["id"]
        
        # Verify it wasn't processed by another instance in the meantime
        if db.check_classification_result_not_in_process(classifier_id, result_id):
            continue 

        try:
            # Run your custom logic
            final_result, indicators = analyze_page(result, helper)
            
            # Save Indicators to the database
            for indicator_name, value in indicators.items():
                db.insert_indicator(indicator_name, str(value), classifier_id, result_id, job_server)
            
            # Save Final Classification Result
            db.update_classification_result(str(final_result), result_id, classifier_id)

        except Exception as e:
            print(f"Error classifying result {result_id}: {e}")
            db.update_classification_result("classifier_error", result_id, classifier_id)
```

### 3.7. Database Registration
Once your code is ready, log into your PostgreSQL database and add an entry to the `classifier` table[cite: 11, 13].
*   **`name`**: Must be the exact name of your folder and Python file (e.g., `my_analyzer`).
*   **`display_name`**: The friendly name that users will see in the frontend Web Interface.

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
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007.