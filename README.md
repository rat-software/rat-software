[![DOI](zenodo.19453057.svg)](https://doi.org/10.5281/zenodo.14049810)

# RAT

The Result Assessment Tool (RAT) is the Free Open-Source Research Toolbox for Collecting, Analyzing and Evaluating Search Results. Identify search queries, collect the matching search results from various search systems, such as Google and Bing, analyze them, and have them evaluated by jurors. RAT can help you with all these tasks and more. It is developed by the research group Search Studies at the Hamburg University of Applied Sciences in Germany. The RAT project is funded by the German Research Foundation (DFG –Deutsche Forschungsgemeinschaft) from 2021 until 2024, project number 460676551 and from 2024 - 2028, project number 557366357.

## Repository Structure

* [rat_backend](./rat-backend): The core API and logic of the tool.
* [rat_frontend](./rat-frontend): The web-based user interface.
* [rat_storage](./rat-storage): Service for handling web data and PDF storage (Required).
* [rat_extension](./rat-extension): Browser extension for scraping search results.

## Contributors to RAT

- #### Project Lead: [Professor Dirk Lewandowski](https://searchstudies.org/team/dirk-lewandowski/) - https://github.com/dirklew
- #### Lead Software Engineer and Developer: [Sebastian Sünkler](https://searchstudies.org/team/sebastian-suenkler/) - https://github.com/sebsuenkler
- #### Software Engineer and Developer: Björn Quast - https://github.com/bjoern-quast
- #### Current Frontend Developer and Assistant: [Tuhina Kumar](https://searchstudies.org/team/tuhina-kumar/) - https://github.com/tuhinak
- #### Former Frontend Developer: Nurce Yagci - https://github.com/yagci
- #### Usability and User Experience Specialist: [Sebastian Schultheiß](https://searchstudies.org/team/schultheiss/) - https://github.com/SebastianSchultheiss
- #### Marketing Manager: [Oliver Koop](https://searchstudies.org/team/oliver-koop/) - https://github.com/oliverkoop-haw
- #### Student Assistant for Software Engineering: [Sophia Bosnak](https://searchstudies.org/team/sophia-bosnak/) - https://github.com/kyuja

Here is the polished, structurally optimized, and typo-free version of your installation manual. 

I cleaned up the layout, fixed the broken markdown backticks and redundant headers, grouped the installation methods logically (Full vs. Component-by-Component), and put the command sequences into clean, copy-pasteable blocks.

***

# ⚙️ Unified RAT Installation & Deployment Manual

The Result Assessment Tool (RAT) is a free, open-source research toolbox for collecting, analyzing, and evaluating search results from engines like Google and Bing. 

This manual provides comprehensive instructions for deploying the RAT ecosystem. You can install all applications on a single server (monolithic deployment) or split them across multiple instances to distribute the workload (e.g., dedicated backend scraping servers and a separate frontend UI server).

---

## 🏗️ Architecture Overview

The RAT ecosystem consists of four core components:

* **Storage Service:** A microservice handling file uploads (HTML, PDFs, screenshots).
* **Frontend (Web Interface):** A Flask application for user, study, and data management.
* **Backend Engine:** A data engine managing web scraping, query sampling, and classification.
* **Browser Extension:** A Manifest V3 Chrome extension for client-side search engine scraping.

---

## 🛠️ 1. Global Prerequisites & Database Setup

Before installing individual components, ensure your server environment is properly configured.

### System Requirements
* **Python 3.12+**
* **Google Chrome / Chromium** (required for the Backend scraper)
* **PostgreSQL** (the central database where all results are stored)

### Database Initialization
Create the database and import the base schema shared by all ecosystem applications:

```bash
createdb -T template0 dbname
psql dbname < install-database/rat-db-install.sql
```

---

## 📦 2. Option A: Full Monolithic Installation

If you intend to host all modules on a single server, you can configure the entire environment at once. 

### Automated Setup
Run the automated script from the root folder:
```bash
chmod +x setup.sh && ./setup.sh
```

### Manual Setup
Alternatively, you can install the global requirements manually:
```bash
python -m venv venv_rat
source venv_rat/bin/activate
python -m pip install -r requirements_rat.txt
```

> 💡 **Next Step:** After completing the global setup, navigate to the individual component directories to configure their specific environment files and systemd services as outlined below.

---

## 🧩 3. Option B: Component-by-Component Installation

Use this approach for custom, distributed deployments or to manually configure specific layers of the monolithic setup.

### 📄 3a. Storage Service Installation
The Storage Service manages all scraped data and must be network-accessible by both the Frontend and Backend.

#### Setup & Configuration
1. Run the local environment script:
   ```bash
   chmod +x setup.sh && ./setup.sh
   ```
2. Edit `storage_service.py` to define your custom `API_KEY` and `STORAGE_FOLDER`.
3. Edit `clean_orphans.py` and supply your PostgreSQL `DB_URI`.

#### Systemd Deployment
```bash
# Copy the service file to the system directory
sudo cp rat-storage.service /etc/systemd/system/rat-storage.service

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable --now rat-storage.service
```

---

### 🖥️ 3b. Frontend (Web Interface) Installation
The web interface connects to the PostgreSQL database and the Storage Service to manage research studies.

#### Environment Setup
```bash
python3 -m venv venv_rat-frontend
source venv_rat-frontend/bin/activate
python -m pip install -r requirements_rat_frontend.txt
```

#### Configuration (`.env`)
Configure your `.env` file with the following required parameters:
* `SQLALCHEMY_DATABASE_URI`: Your PostgreSQL connection string.
* `STORAGE_BASE_URL` / `API_UPLOAD_KEY`: Must match the Storage Service URL and API key defined in step 3a.
* `MAIL_SERVER` / `MAIL_PORT`: Essential for user registration. The environment defaults to **Resend** (`smtp.resend.com` on port `465`), but any valid SMTP provider works. Ensure the sender email is declared via `SECURITY_EMAIL_SENDER` (e.g., `admin@yourdomain.com`).

#### Bypass SMTP / Manual User Creation
If you are developing locally or do not want to configure an SMTP server, you can bypass email confirmation and create active, pre-confirmed users directly via the CLI:
```bash
python add_rat_user.py
```

#### Database Initialization & Production Deployment
```bash
# Run database migrations
export FLASK_APP=rat.py
flask db upgrade
```

Create a systemd service file at `/etc/systemd/system/rat-frontend.service` using **Gunicorn** to serve the `wsgi:app` entry point, then run:
```bash
sudo systemctl enable --now rat-frontend.service
```

---

### 🌐 3c. Nginx Reverse Proxy & SSL Setup
When running the Frontend and Storage services on the same server, use Nginx to cleanly route external traffic.

* **Frontend** runs locally on port `5000`
* **Storage Service** runs locally on port `5001`

#### Nginx Configuration Block
Configure your server block to map the locations, ensuring you increase the maximum body size to handle large payload ZIP files:

```nginx
server {
    server_name your_domain.com;

    # Frontend Web Interface
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Storage Service
    location /storage {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        client_max_body_size 100M;
    }
}
```

#### SSL Encryption
Secure your web traffic using Let's Encrypt Certbot:
```bash
sudo certbot --nginx -d your_domain.com
```

---

### 🚀 3d. Backend Engine Installation
The backend handles heavy-lifting operations. It utilizes a Unified Controller to manage the Scraper, Query Sampler, and Classifier.

#### Environment Setup
```bash
python -m venv venv_rat_backend
source venv_rat_backend/bin/activate
python -m pip install -r requirements_rat_backend.txt
```
> ⚠️ **Dependency Note:** Ensure that `chromium-chromedriver` is installed and explicitly available on your system's global environment path.

#### Configuration
Update the configuration templates located inside the `/config` directory:
* **`config_db.ini`**: Set your PostgreSQL connection credentials.
* **`config_sources.ini`**: Define your job server metadata and storage API keys.
* **`google-ads.yaml`**: Update with developer tokens for the Query Sampler module.

#### Production Deployment
Create a systemd service file (`/etc/systemd/system/rat-backend.service`). Ensure your service directives are explicitly configured to handle process lifecycles cleanly:
* Set `ExecStart` to point to `backend_controller_start.py`.
* Set `ExecStop` to point to `backend_controller_stop.py` to safely terminate Chromium processes and clear orphaned backend jobs during restarts.

```bash
sudo systemctl enable --now rat-backend.service
```

---

### 🧩 3e. Browser Extension Setup (Client-Side)
For crowdsourced or user-driven data collection, RAT leverages a high-performance Manifest V3 Chrome extension.

1. Download or clone the extension repository to your local machine.
2. Open Google Chrome and navigate to `chrome://extensions/`.
3. Toggle **Developer mode** on in the top-right corner.
4. Click **Load unpacked** in the top-left corner.
5. Select the root directory containing the extension's `manifest.json` file.
6. Click the extension icon in your browser toolbar to open the RAT Scraper sidepanel to configure target studies and proxy pools.

## RAT Extensions

The repository provides an overview of extensions created by our developer community: [rat-extensions (RAT extensions) · GitHub](https://github.com/rat-extensions)

- **Imprint Crawler**: A web crawler that is able to automatically extract legal notice information from websites while taking German legal aspects into account: [GitHub - rat-extensions/imprint-crawler · GitHub](https://github.com/rat-extensions/imprint-crawler). Developed by Marius Messer - [MnM3 · GitHub](https://github.com/MnM3)
- **Readability Score**: A Python tool that extracts the main text content of a web document and analyzes its readability: [GitHub - rat-extensions/readability-score: A python tool that extracts the main text content of a web document and analysis it readability. · GitHub](https://github.com/rat-extensions/readability-score). Developey by Mohamed Elnaggar - [mohamedsaeed21 · GitHub](https://github.com/mohamedsaeed21)
- **Forum Scraper**: An extension to extract comments from German online news services: [https://github.com/rat-software/forum-scraper](https://github.com/rat-extensions/forum-scraper). Developed by Paul Kirch - [g1thub-4cc0unt · GitHub](https://github.com/g1thub-4cc0unt)
- **EI_Logger_BA**: A browser extension for conducting interactive information retrieval studies. With this extension, study participants can work on search tasks with search engines of their choice and both the search queries and the clicks on search results are saved: [GitHub - rat-extensions/EI_Logger_BA · GitHub](https://github.com/rat-extensions/EI_Logger_BA). Developed by Hossam Al Mustafa - [Samustafa (Hossam Al Mustafa) · GitHub](https://github.com/Samustafa)
- **Identifying affiliate links in webpages**: [GitHub - rat-extensions/Identifying-affiliate-links-in-webpages: A python tool that extracts all affiliate links of a web document and scores this webpage according to its number and prominence of affiliate links. Database: · GitHub](https://github.com/rat-extensions/Identifying-affiliate-links-in-webpages). Developed by Philipp Krueger - [PhilippUDE · GitHub](https://github.com/PhilippUDE)
- **App Reviews Scraper**: [GitHub - rat-extensions/app-reviews-scraper: As a part of my Bachelor thesis I developed these app reviews scrapers, that will visit designated URLs of a set of applications and export the scraped reviews and relevant information. This is to be served as an extension to the Result Assessment Tool (RAT) and explicitly for research purposes only. · GitHub](https://github.com/rat-extensions/app-reviews-scraper). Developed by Tanveer Ahmed - [https://github.com/PhilippUDE](https://github.com/tanveerx/)
- **Visualizations of IR measures**: [GitHub - rat-extensions/ir-evaluation: Visualizations of IR measures · GitHub](https://github.com/rat-extensions/ir-evaluation). Developed by Ritu Suhas Shetkar - [ritushetkar · GitHub](https://github.com/ritushetkar)
- **Scraping News Articles**: [GitHub - rat-extensions/NewsArticlesScraper: This Python tool retrieves the homepages of given news portals and scrapes the HTML text of the articles found. · GitHub](https://github.com/rat-extensions/NewsArticlesScraper). Developed by Esther von der Weiden - [EstherKuerbis · GitHub](https://github.com/EstherKuerbis/)

---

## 📜 License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
