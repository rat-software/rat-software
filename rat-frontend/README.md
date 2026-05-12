# RAT Frontend (Web Interface)

The primary user interface for managing studies, participants, and search engine analysis. This Flask application connects to a PostgreSQL database and interacts with the RAT Storage Service for file management.

---

## 🛠️ 0. Prerequisites

Before installing the backend, ensure your server has the following:
* **python3 3.12**

---

## 🛠 1. Installation & Environment

### Step 1: Create Virtual Environment
Navigate to your frontend project directory and run:
```bash
python3 -m venv venv_rat-frontend
source venv_rat-frontend/bin/activate
```

### Step 2: Install Dependencies
Ensure you have the latest pip version and install the required packages:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements_rat_frontend.txt
```

---

## ⚙️ 2. Configuration

You must configure the application by editing `.env`. Use the table below as a guide:

| Setting | Description | Example Value |
| :--- | :--- | :--- |
| **SQLALCHEMY_DATABASE_URI** | PostgreSQL connection string | `'postgresql://user:pass@localhost:5432/db'` |
| **SECRET_KEY** | Random string for session security | Use `os.urandom(24)` to generate |
| **SECURITY_PASSWORD_SALT** | Salt for password hashing | A long random string |
| **STORAGE_BASE_URL** | URL of your Storage Service | `'https://storage.yourdomain.com'` |
| **API_UPLOAD_KEY** | Must match the Storage Service Key | `'your-secure-api-key'` |

## 📧 2.1 E-Mail Setup (Required for Registration)

The application requires an active SMTP connection to send confirmation and password reset emails. **Without this configuration, new users and participants will not be able to complete the registration process or activate their accounts.**

[cite_start]The environment is set up to use **Resend** by default, but any valid SMTP provider can be used. Ensure the following values are correctly populated in your `.env` file:

| Setting | Description | Example Value / Default |
| :--- | :--- | :--- |
| **MAIL_SERVER** | The SMTP server address | [cite_start]`smtp.resend.com` |
| **MAIL_PORT** | The port for secure SMTP | [cite_start]`465` |
| **MAIL_PASSWORD** | Your SMTP password or Resend API Key | `re_123456789...` |
| **SECURITY_EMAIL_SENDER** | The email address users will see as the sender | [cite_start]`admin@yourdomain.com` |

### Alternative: Adding Users Without E-Mail Setup
If you cannot or do not want to configure an SMTP server (e.g., for local development), you can manually add pre-confirmed, active users directly via the command line using the provided script. This bypasses the email confirmation requirement completely:

```bash
python add_rat_user.py
```
---

## 🗄 3. Database Initialization

Since the app uses `Flask-Migrate`, you need to initialize the database schema before starting the service:

```bash
export FLASK_APP=rat.py
flask db init
flask db upgrade
```

---

## 🖥 4. Production Deployment (Linux Service)

To run the frontend as a persistent background service, we use **Gunicorn** and **systemd**.

### Step 1: Create the Service File
Create a new file at `/etc/systemd/system/rat-frontend.service`:

```ini
[Unit]
Description=Gunicorn instance to serve RAT Frontend
After=network.target

[Service]
User=your_username
Group=www-data
WorkingDirectory=/var/www/rat/frontend
Environment="PATH=/var/www/rat/frontend/venv_rat_frontend/bin"
# Executing via the wsgi.py entry point
ExecStart=/var/www/rat/frontend/venv_rat_frontend/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

### Step 2: Enable and Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable rat-frontend.service
sudo systemctl start rat-frontend.service
```

---

## 🛠 5. Management & Logs

| Action | Command |
| :--- | :--- |
| **Check Status** | `sudo systemctl status rat-frontend.service` |
| **Restart App** | `sudo systemctl restart rat-frontend.service` |
| **View Live Logs** | `sudo journalctl -u rat-frontend.service -f` |

---

## 🧹 6. Local Testing (Development)
For local development and debugging, you can run the app directly using the `rat.py` entry point:
```bash
export FLASK_APP=rat.py
export FLASK_ENV=development
flask run
```
Since you're using Nginx, it's the perfect way to wrap everything together. It acts as a "front door," handling SSL termination and routing traffic to your two separate Gunicorn services (Frontend and Storage).

Here is the updated manual and configuration for your Linux server.

---

## 🌐 7. Nginx Reverse Proxy Configuration

Nginx will sit in front of your Flask apps. [cite_start]This configuration assumes your **Frontend** runs on port `5000` and your **Storage Service** runs on port `5001`[cite: 1].

### Step 1: Create the Nginx Site Config
Create a new file: `sudo nano /etc/nginx/sites-available/rat-software`

```nginx
server {
    listen 80;
    server_name your_domain.com; # Replace with your actual domain

    # 1. RAT Frontend
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 2. RAT Storage Service
    # Routed to /storage to match the app's internal logic
    location /storage {
        proxy_pass http://127.0.0.1:5001/; # Note the trailing slash
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase upload limit for large ZIP files
        client_max_body_size 100M;
    }
}
```

### Step 2: Enable the Configuration
```bash
# Link to sites-enabled
sudo ln -s /etc/nginx/sites-available/rat-software /etc/nginx/sites-enabled/

# Test the syntax
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## 🔒 8. Securing with SSL (Certbot)

Since your `config.py` is set to `PREFERRED_URL_SCHEME = 'https'`, you should secure the connection immediately.

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

---

## 🔄 9. Maintenance & Troubleshooting

### Log Locations
When things go "thump" in the night, these are your three best friends:
* **Frontend Logs**: `sudo journalctl -u rat-frontend.service -f`
* **Storage Logs**: `sudo journalctl -u rat-storage.service -f`
* **Nginx Error Logs**: `sudo tail -f /var/log/nginx/error.log`

### Static Files
If your CSS or JS isn't loading, ensure Nginx has permission to read your project folder. You may need to add a specific `location /static/` block to your Nginx config if Gunicorn isn't serving them directly.

### Updating the App
When you pull new code from your repository:
1.  **Activate Venv**: `source venv/bin/activate`
2.  **Update Deps**: `pip install -r requirements_rat_frontend.txt`
3.  **Migrate DB**: `flask db upgrade`
4.  **Restart**: `sudo systemctl restart rat-frontend`

---

### Final Check: Configuration Sync
Ensure your `config.py` matches your Nginx setup:
* **`STORAGE_BASE_URL`**: Should be `https://your_domain.com/storage`.
* **`APPLICATION_ROOT`**: Is set to `/`.
* **`SESSION_COOKIE_PATH`**: In the storage service, this is correctly set to `/storage` to avoid collisions.

---

## 📜 License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
