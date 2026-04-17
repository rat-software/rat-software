# RAT Storage Service

A dedicated Flask-based microservice designed to store, manage, and serve scraped data (HTML sources, screenshots, and PDFs). This service includes automated cleanup utilities and secure access via timed tokens.

## 🚀 Features

* **Secure Uploads**: API-Key restricted file uploads for the scraper.
* **Encapsulated Storage**: Serves specific files (HTML/JPG) directly from inside ZIP archives.
* **Timed Access**: Uses `itsdangerous` URL signatures to prevent unauthorized file access.
* **Maintenance**: Includes a cleanup script to remove "orphaned" files not present in the database.

---

## 🛠 Project Structure

* `storage_service.py`: The main Flask application (Storage API).
* `clean_orphans.py`: Maintenance utility to sync physical storage with the database.
* `rat-storage.service`: Systemd configuration file for Linux deployment.
* `setup.sh`: Automated environment setup script.

---

## 📦 1. Installation & Configuration

### Automated Setup
First, run the setup script to create the directory structure and the Python virtual environment:
```bash
chmod +x setup.sh
./setup.sh
```

### Configuration
Before starting, you **must** update the following files with your server-specific details:

1.  **`storage_service.py`**: Set your `API_KEY` and `STORAGE_FOLDER`.
2.  **`clean_orphans.py`**: Set your `DB_URI` (PostgreSQL connection) and `STORAGE_DIR`.
3.  **`rat-storage.service`**: Update the `User`, `Group`, `WorkingDirectory`, and `ExecStart` paths to match your server's username and project location.

---

## ⚙️ 2. Deployment (Linux Service)

To ensure the app starts automatically on boot and restarts if it crashes, configure it as a **systemd** service.

### Step 1: Install the Service File
Copy the provided service file to the system directory:
```bash
sudo cp rat-storage.service /etc/systemd/system/rat-storage.service
```

### Step 2: Enable and Start
Run the following commands to reload the system manager and start your service:
```bash
# Reload systemd to recognize the new file
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable rat-storage.service

# Start the service now
sudo systemctl start rat-storage.service
```

---

## 🛠 3. Management & Monitoring

### Check Service Status
To see if the app is running correctly:
```bash
sudo systemctl status rat-storage.service
```

### Viewing Logs
If the app isn't behaving as expected, check the live logs:
```bash
# View the last few lines and follow new output
sudo journalctl -u rat-storage.service -f
```

### Restarting/Stopping
```bash
sudo systemctl restart rat-storage.service
sudo systemctl stop rat-storage.service
```

---

## 🧹 4. Maintenance (Orphan Cleanup)

Over time, files may exist on disk that are no longer referenced in your database. To keep the server clean, run the maintenance utility:

1.  **Manual Run**:
    ```bash
    source venv/bin/activate
    python clean_orphans.py
    ```
2.  **Automated (Cron)**: 
    You can schedule this script to run weekly. Open your crontab (`crontab -e`) and add:
    ```bash
    0 3 * * 1 /path/to/project/venv/bin/python /path/to/project/clean_orphans.py >> /var/log/rat-cleanup.log 2>&1
    ```
    *This runs the cleanup every Monday at 3:00 AM.*

---

## 🧪 5. Testing the Deployment

Once the service is active, run the test script to ensure the API is reachable and the security tokens are working:
```bash
python test_api.py
```

---

## 📜 License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007