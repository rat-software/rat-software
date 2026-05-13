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
* 
`rat-storage.service`: Systemd configuration file for Linux deployment.


* `setup.sh`: Automated environment setup script.
* 
`.env`: Centralized configuration file for all environment variables (if necessary, copy from `.env.tpl`).


* 
`requirements_rat_storage.txt`: Python dependency list.

---

## 📦 1. Installation & Configuration

### Automated Setup

First, run the setup script to create the directory structure and the Python virtual environment:

```bash
chmod +x setup.sh
./setup.sh

```

### Configuration (.env)

The service uses a `.env` file for all critical settings. Copy the file named `.tpl.env` to `.env` in the root directory and fill in your server-specific details:

```bash
# Database (used by clean_orphans.py)
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/db 

# Storage Service Configuration
STORAGE_BASE_URL=http://localhost:5001 
API_UPLOAD_KEY=your-secure-key-here 
STORAGE_FOLDER=/var/www/rat/storage 

```

## ⚙️ 2. Deployment (Linux Service)

To ensure the app starts automatically on boot and restarts if it crashes, configure it as a **systemd** service using the provided configuration.

### Step 1: Change the User and the paths to the WorkingDirectory, Environment and ExecStarts according to your system and install the Service File 

For Example
```bash
[Unit]
Description=Gunicorn instance to serve RAT Storage Service
After=network.target

[Service]
User=test
Group=www-data
WorkingDirectory=/home/test/rat-storage
Environment="PATH=/home/test/rat-storage/venv_rat_storage/bin"
ExecStart=/home/test/rat-storage/venv_rat_storage/bin/gunicorn --workers 3 --bind 0.0.0.0:5001 storage_service:app

[Install]
WantedBy=multi-user.target
```

Copy the service file to the system directory:

```bash
sudo cp rat-storage.service /etc/systemd/system/rat-storage.service

```

### Step 2: Enable and Start

Run the following to recognize the new file and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable rat-storage.service

# Start now
sudo systemctl start rat-storage.service

```

---

## 🛠 3. Management & Monitoring

### Check Service Status

Verify the service is active and running:

```bash
sudo systemctl status rat-storage.service

```

### Viewing Live Logs

Monitor incoming requests or errors in real-time:

```bash
sudo journalctl -u rat-storage.service -f

```

---

## 🧹 4. Maintenance (Orphan Cleanup)

Use the cleanup utility to remove files from the storage folder that are no longer referenced in the database:

1. **Manual Run**:
```bash
source venv_rat_storage/bin/activate
python3 clean_orphans.py

```


2. **Automated (Cron)**:
Add this to your crontab (`crontab -e`) to run every Monday at 3:00 AM:
```bash
0 3 * * 1 /home/test/rat-storage/venv_rat_storage/bin/python3 /home/test/rat-storage/clean_orphans.py >> /var/log/rat-cleanup.log 2>&1

```



---

## 🧪 5. Testing the Deployment

Once the service is active, run the test script to ensure the API is reachable and the security tokens are working:

```bash
python3 test_api.py

```

---

## 📜 License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

