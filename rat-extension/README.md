## RAT Browser Extension (Scraper)

The **Result Assessment Tool (RAT) Scraper** is a Manifest V3 browser extension for automated data collection from search engines (**Google, Bing, DuckDuckGo, YouTube** and your own engine definitions). It collects organic results, ads and AI-generated overviews. Studies are built in the extension's sidepanel; the extension works as a stand-alone tool (no server needed) and can also run unattended in the background on a server, in a container or on a second PC.

---

### Key Features

* **Multi-Engine Support**: Google, Bing, DuckDuckGo, YouTube, plus custom engines (JSON, editable in the sidepanel).
* **AI Data Extraction**: Extracts text and citations from Google AI Overviews and Bing Chat where present.
* **Human-like Behaviour** (all switchable per study, see *Behaviour options*):
  * Lognormal pacing instead of uniform random waits.
  * Real (trusted) mouse movement, wheel scrolling and clicks on the "next page" link via the Chrome DevTools protocol.
  * Optional typed search: the query is typed key by key (with rare typos that are corrected) into the real search box.
  * Optional random order of tasks and regular longer breaks.
* **Proxies**: list mode (IP:Port:User:Pass, e.g. Webshare) and gateway mode (residential providers with one endpoint and a session in the user name). Per-IP cooldown, optional request budget per IP, cookies are cleared on every rotation, a "Test proxies" button shows the exit IP of each proxy.
* **CAPTCHA recovery**: rotates to the next usable IP, otherwise waits for the earliest cooldown and resumes automatically. The proxy is released while a study is paused or finished.
* **Unattended operation**: studies survive service-worker and browser restarts; several studies can be queued (one runs at a time); studies can repeat on a schedule; an optional webhook (JSON POST, events `finished`, `captcha`, `attention`) reports the status.
* **Live metrics** per study: pages, results, zero-result pages, captchas, rotations, per-engine/country breakdown. A streak of empty result pages pauses the study instead of silently collecting nothing.
* **IndexedDB persistence**: sessions, results and logs are stored locally.

---

### Architecture Overview

* **Background Worker (`background.js`)**: scheduler, queue, captcha/proxy logic, persistence. A watchdog alarm (every minute) restarts runs that lost their worker.
* **`lib/proxy.js`**: proxy parsing, rotation state, authentication, tests.
* **`lib/human.js`**: pacing and trusted input (mouse, wheel, keys).
* **Content Script (`content.js`)**: DOM extraction, captcha detection.
* **Sidepanel UI (`sidepanel.html`/`.js`)**: study builder and dashboard.
* **`engines/*.json`**: engine definitions (selectors, URL parameters, optional `typing` block for typed search).

---

### Important Preliminary Information

Back up your session results before updating the extension. Do not change the IndexedDB version (`RAT_Database` v8) when modifying the code.

---

### Installation

1. Clone or download this repository.
2. Open Chrome and navigate to `chrome://extensions/`.
3. Enable **Developer mode**.
4. Click **Load unpacked** and select the directory that contains `manifest.json`.
5. Click the **RAT Scraper** icon to open the sidepanel.

> Note: Chrome 137 and newer (branded builds) ignore the `--load-extension` command line flag. Loading via the UI as above still works. For automatic start-up (servers/containers) use Chromium or "Chrome for Testing", see *Running unattended*.

---

### Configuration & Usage

#### 1. Creating a Study

* **Queries**: keywords, one per line.
* **Engines**: combine engines, countries and languages.
* **Limit**: target number of results or pages per task.
* **Delays**: min/max seconds between requests (this is the median range for the lognormal pacing).
* **Proxies**: tick "Use proxies" and paste one proxy per line.

Accepted proxy formats:

```
IP:Port                         (no authentication)
IP:Port:User:Pass               (Webshare "Proxy list" export, passwords may contain ':')
User:Pass@IP:Port
http://User:Pass@IP:Port
```

**Mode "List"**: every line is one IP; the extension rotates through them (least recently used first) and puts an IP on cooldown after a captcha.

**Mode "Gateway"** (residential providers): one line with the provider's endpoint. The *username template* decides how a new exit IP is requested; placeholders are `{user}`, `{session}` (random id, new on every rotation) and `{rand}`. Example: `{user}-session-{session}`. Check your provider's documentation for the exact syntax.

Use **Test proxies** to see whether authentication works and which exit IP each proxy has. Tests are refused while a study is running (the proxy setting is global for the browser profile).

SOCKS proxies with credentials are not supported by Chrome and are rejected when entered.

#### 2. Behaviour options (collapsible panel in the create view and while a study is open)

| Option | Effect |
| --- | --- |
| Human pacing | Lognormal waits, small random pauses. |
| Trusted input | Real mouse/wheel/click events through the debugger API (shows Chrome's "debugging" banner). |
| Typed search *(experimental)* | Opens the engine's home page and types the query. Falls back to a direct URL if the search box is not found. Country/language parameters of the engine may behave differently than with direct URLs, so check a sample first. |
| Shuffle | Random task order. |
| Break every N tasks | A longer pause of min–max seconds every N tasks. |
| Max captcha rounds | After this many captcha rounds the study stays paused. |
| Webhook | URL (http/https) that receives a small JSON POST (`event`, `text`) on `finished`, `captcha` (IP switched / waiting) and `attention` (manual action needed). |
| Repeat | Re-run the whole study every X hours, N times (creates a new run). |
| Request budget / cooldown | Maximum requests per IP before rotating, minutes an IP rests after a captcha. |

#### 3. Managing Captchas

1. With proxies: the extension rotates to the next IP that is not cooling down and continues.
2. If all IPs are cooling down, the study waits until the first one is available again (shown in the status box) and resumes automatically.
3. Without proxies or after the maximum number of rounds, the captcha tab stays open for a manual solve; the study resumes when it is solved.

#### 4. Exporting Data

* **CSV**: queries, ranks, titles, AI overview texts, ads.
* **ZIP**: CSV, logs and, if enabled, saved SERP data.
* **Study design export/import**: shares the study set-up only. Results, proxy lists and webhook URLs are removed on export.

#### 5. Add your own engine

1. Open the engines manager in the sidepanel.
2. Create a new engine: base URL, query parameter and CSS selectors (container, title, URL, snippet, next link).
3. Optional: add a `typing` block (`homeUrl`, `inputSelectors`, `submit`) to allow typed search.
4. Export/import engines as JSON to share them.

---

### Running unattended (server, container, second PC)

The extension has to run inside a real, non-headless browser window; headless Chrome is detected much more easily. A virtual display is enough.

* **Second Windows PC / VM**: run `powershell -ExecutionPolicy Bypass -File deploy\start-windows.ps1 -Chrome "C:\path\to\chrome.exe"` (Chrome for Testing or Chromium; branded Chrome 137+ ignores the load flag, so load the extension once via `chrome://extensions` in that dedicated profile). Create the study, press Start and leave the machine running. The script keeps Windows from sleeping. The screen may turn off, but do not lock the session or minimise the window; a locked session can throttle the browser. A VM or an RDP/VNC session that stays connected is the safest choice.
* **Docker (Linux)**: `deploy/` contains a Dockerfile, `docker-compose.yml` and `start.sh` with Chromium, a virtual display (Xvfb) and a small web viewer (noVNC). Start with `docker compose -f deploy/docker-compose.yml up -d --build` and open `http://localhost:6080/vnc.html` to build studies in the sidepanel or solve captchas. Port 6080 is bound to localhost only; use an SSH tunnel for remote access and set `VNC_PASSWORD`. Profile data (IndexedDB with your results) lives in the `rat-profile` volume.

Set it up once, create the study (in the sidepanel through the web viewer), start it and close the viewer. The study continues; the watchdog restarts it after crashes or browser restarts, the webhook tells you when it finished.

Studies and results live in the browser profile. Back up the volume/profile directory or use the export button.

---

### Known limits

* The extension cannot be validated against live Google/Bing behaviour automatically; captcha rates depend on IP quality, query volume and region. Datacenter proxies are flagged far more often than residential ones.
* Typed search and trusted input have only been tested against a local mock server, not against live search engines.
* There is no remote coordinator/worker mode; each browser runs its own studies.
* No bandwidth/volume counter for metered residential proxies (the request budget per IP counts requests, not bytes).
* A study set to run only in certain hours ("active hours") is not implemented.

---

### Permissions used in `manifest.json`

* `debugger`: trusted input (mouse, wheel, keys) and screenshots.
* `proxy` & `webRequest` & `webRequestAuthProvider`: IP rotation and proxy authentication (credentials are only given to the configured proxy, never to websites).
* `cookies` & `browsingData`: cookie clearing on proxy rotation.
* `alarms`: watchdog and scheduled retries.
* `storage` & `unlimitedStorage`: local persistence.
* `power`: prevents the system from sleeping during a study.

---

## License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
