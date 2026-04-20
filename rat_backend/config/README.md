# ⚙️ RAT Configuration Folder

This folder serves as the central settings hub for the RAT Backend applications. All files are provided with **placeholders** to keep the repository secure while providing a clear template for your own environment.

## 🚀 Getting Started

1.  Identify the three configuration files in the backend structure.
2.  Replace all placeholder values (e.g., `your_db`, `your_api_key`) with your actual credentials.
3.  **Security Note**: Never commit your finalized files with real credentials to a public repository.

---

## 🗄️ 1. Database Configuration (`config_db.ini`)

This file enables backend workers to communicate with your PostgreSQL database.

| Parameter | Placeholder | Description |
| :--- | :--- | :--- |
| **database** | `your_db` | The name of your RAT database. |
| **user** | `your_user` | The database username. |
| **host** | `db_ip` | The IP address or hostname of your database server. |
| **port** | `db_port` | The connection port (default is `5432`). |
| **password** | `db_pass` | The password for the specified database user. |

---

## 🕸️ 2. Scraper & Storage Settings (`config_sources.ini`)

This file configures the behavior of the Selenium-based scraper and its connection to the storage microservice.

* **`job_server`**: A unique name for this scraper instance (e.g., `your_server`).
* **`wait_time`**: Seconds the browser waits to ensure full page rendering.
* **`api-key`**: Your secret key for authenticating with the **RAT Storage Service**.
* **`storage-url`**: The full upload endpoint (e.g., `your_storage_url`).

---

## 🔍 3. Google Ads API (`google-ads.yaml`)

Required for the **Query Sampler** module to discover new keywords. This file is located in the `query_sampler/` directory but is a core part of the system configuration.

| Key | Placeholder | Description |
| :--- | :--- | :--- |
| **developer_token** | `your_developer_token` | Your unique Google Ads developer token. |
| **client_id** | `your_client_id` | Your Google Cloud OAuth2 client ID. |
| **client_secret** | `your_client_secret` | Your Google Cloud OAuth2 client secret. |
| **refresh_token** | `your_refresh_token` | The token generated via `generate_user_credentials.py`. |
| **login_customer_id** | `your_manager_id` | Your manager account ID (if applicable). |

---

## 📜 License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007