## RAT Browser Extension (Scraper)

The **Result Assessment Tool (RAT) Scraper** is a high-performance, Manifest V3 browser extension designed for automated data collection from search engines like **Google** and **Bing**. It automates the collection of organic results, paid advertisements, and AI-generated overviews (SGE/Bing Chat) while simulating human browsing behavior to mitigate bot detection.

---

### 🚀 Key Features

* **Multi-Engine Support**: Seamlessly switch between Google and Bing configurations.
* **AI Data Extraction**: Automatically detects and extracts full text and citations from Google AI Overviews and Bing Chat.
* **Human Simulation**: Uses non-linear smooth scrolling, random mouseovers, and variable idle delays to mimic human users.
* **Proxy Rotation & Auth**: Supports "fixed_servers" proxy mode with full username/password authentication injection.
* **CAPTCHA Recovery**: Intelligent bot-detection handling with automated proxy rotation or timed retries via Chrome Alarms.
* **IndexedDB Persistence**: Local storage of session metadata, logs, raw HTML, and high-quality page screenshots.

---

### 🛠 Architecture Overview

The extension is built on a distributed architecture to ensure stability during long-running scraping sessions:

* **Background Worker (`background.js`)**: The "brain" of the operation. Manages the IndexedDB, proxy rotation, and the global task queue.
* **Content Script (`content.js`)**: The "worker." Injected into search pages to manipulate the DOM, extract data, and detect CAPTCHAs.
* **Sidepanel UI (`sidepanel.html`/`.js`)**: The "controller." Provides a real-time dashboard for monitoring logs and managing studies.

---

### 📦 Installation

1. Clone or download this repository.
2. Open Chrome and navigate to `chrome://extensions/`.
3. Enable **Developer mode** (top right toggle).
4. Click **Load unpacked** and select the directory containing the `manifest.json` file.
5. Click the **RAT Scraper** icon to open the sidepanel.

---

### ⚙️ Configuration & Usage

#### 1. Creating a Study

* **Queries**: Enter keywords line-by-line.
* **Engines**: Combine different countries (US, DE, UK, etc.) and languages for each keyword.
* **Limit**: Define the target number of organic results to collect per task.

#### 2. Managing Captchas

When a CAPTCHA is detected, the extension will:

1. Attempt to rotate to a new proxy (up to 3 times).
2. Pause and alert the user for a manual solve.
3. Set an alarm to retry automatically after a cooldown period (5, 15, 30, or 60 minutes).

#### 3. Exporting Data

* **CSV**: A structured file containing queries, ranks, titles, and AI overview texts.
* **ZIP**: A full archive containing the CSV, activity logs, raw HTML files, and JPG screenshots.

---

### 🔒 Permissions used in `manifest.json`

* `debugger`: Used for capturing screenshots beyond the visible viewport.
* `proxy` & `webRequest`: Essential for rotating IP addresses and injecting authentication.
* `storage` & `unlimitedStorage`: Required for local IndexedDB persistence.
* `power`: Prevents the system from entering sleep mode during active scraping.

---

### 📜 License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007