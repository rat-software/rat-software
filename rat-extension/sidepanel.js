/**
 * @file sidepanel.js - Version 2.1 (Video Export, CSV Formatting)
 * Manages the User Interface of the RAT Browser Extension.
 * Handles user input, session creation, real-time status updates, 
 * heavy-lifting database operations, and the Scraper Sandbox.
 */

// --- 0. DB CONSTANTS & STATE ---
const DB_NAME = "RAT_Database";
const STORE_SESSIONS = "sessions";
const STORE_RESULTS = "results";
const STORE_LOGS = "logs";

let dbLocal;
let currentConfigs = [];
let currentSessionId = null;
let cachedTasks = [];
let currentTaskFilter = "ALL";

let availableEngines = []; 
let currentEditingEngineId = null;

let currentTaskPage = 1;
const TASKS_PER_PAGE = 50;
let panelsFilledFor = null;
let lastStatus = null;


// --- ZOOM LOGIC ---
let currentZoom = parseFloat(localStorage.getItem('rat_ui_zoom')) || 1.0;

function applyZoom(zoomLevel) {
    document.body.style.zoom = zoomLevel;
    localStorage.setItem('rat_ui_zoom', zoomLevel);
}

// --- DYNAMIC SCRAPE LIMIT DEFAULTS ---
document.getElementById('sessLimitType').addEventListener('change', (e) => {
    const limitInput = document.getElementById('sessLimit');
    if (e.target.value === 'PAGES') {
        limitInput.value = 1;
    } else {
        limitInput.value = 10;
    }
});

document.getElementById('liveLimitType').addEventListener('change', (e) => {
    const liveLimitInput = document.getElementById('liveLimit');
    if (e.target.value === 'PAGES') {
        liveLimitInput.value = 1;
        liveLimitInput.placeholder = "Ex: 1";
    } else {
        liveLimitInput.value = 10;
        liveLimitInput.placeholder = "Ex: 10";
    }
});

// --- 0b. PROXY / BEHAVIOR PANELS (shared by the create view "c" and the live view "e") ---
function esc(s) {
    return String(s === undefined || s === null ? "" : s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function proxyPanelHtml(p) {
    return `
    <label>Proxy Mode <span class="tooltip" data-tip="List: every line is its own proxy and they are rotated. Gateway: one rotating endpoint (typical for residential proxies) where a new session token in the username gives a new IP.">?</span></label>
    <select id="${p}ProxyMode">
        <option value="list">List of proxies (e.g. Webshare datacenter)</option>
        <option value="gateway">Gateway / rotating residential</option>
    </select>
    <div id="${p}ProxyTplRow" style="display:none">
        <label>Username template</label>
        <input type="text" id="${p}ProxyTpl" placeholder="{user}-session-{session}">
        <div class="hint">Placeholders: <code>{user}</code> = username from the line, <code>{session}</code> = new random token on every rotation, <code>{rand}</code> = random value. The exact syntax depends on your provider (see its docs).</div>
    </div>
    <div class="row" style="margin-top:8px;">
        <div style="flex:1"><label style="margin-top:0">Rotate after N requests <span class="tooltip" data-tip="Switch to the next IP after this many page loads. 0 = only rotate on captcha or errors.">?</span></label>
            <input type="number" id="${p}ProxyBudget" min="0" value="0"></div>
        <div style="flex:1"><label style="margin-top:0">IP cooldown (min) <span class="tooltip" data-tip="After a captcha an IP is not reused for this long.">?</span></label>
            <input type="number" id="${p}ProxyCooldown" min="1" value="120"></div>
    </div>
    <label class="check-row"><input type="checkbox" id="${p}ProxyClearCookies" checked><span style="text-transform:none; font-weight:normal;">Clear search-engine cookies when the IP changes<small>Recommended: a new IP with the old cookies is easy to link.</small></span></label>
    <div class="hint">Accepted formats: <code>IP:Port:User:Pass</code> (Webshare), <code>User:Pass@IP:Port</code>, <code>http://User:Pass@IP:Port</code>, <code>IP:Port</code>. Lines starting with # are ignored. Only HTTP(S) proxies work with login in Chrome.</div>
    <button type="button" id="${p}ProxyTestBtn" class="btn-secondary btn-sm" style="margin-top:8px;">Test proxies</button>
    <div id="${p}ProxyTestOut" style="margin-top:6px; font-size:11px;"></div>`;
}

function behaviorPanelHtml(p) {
    return `
    <label class="check-row"><input type="checkbox" id="${p}HumanPacing" checked><span style="text-transform:none; font-weight:normal;">Human-like pacing<small>Irregular waiting times (log-normal) instead of uniform random delays.</small></span></label>
    <label class="check-row"><input type="checkbox" id="${p}TrustedInput" checked><span style="text-transform:none; font-weight:normal;">Real mouse &amp; keyboard events<small>Clicks, scrolling and typing are sent as trusted browser input (needs the "debugger" permission; Chrome shows a debugging banner on the search tab).</small></span></label>
    <label class="check-row"><input type="checkbox" id="${p}Shuffle"><span style="text-transform:none; font-weight:normal;">Shuffle task order<small>Avoids hitting the same query across engines/countries in a rigid pattern. Applies to tasks that have not started yet.</small></span></label>
    <label class="check-row"><input type="checkbox" id="${p}TypedSearch"><span style="text-transform:none; font-weight:normal;">Typed search <span class="experimental">experimental</span><small>Open the search engine's start page and type the query like a person instead of opening the result URL directly. Falls back to the direct URL if the field is not found. Not yet verified against live search engines.</small></span></label>
    <label>Break every N tasks <span class="tooltip" data-tip="Take a longer pause (min–max seconds) after this many tasks. 0 = no breaks.">?</span></label>
    <div class="row">
        <input type="number" id="${p}BreakEvery" min="0" value="0" style="flex:1" placeholder="N">
        <input type="number" id="${p}BreakMin" min="0" value="120" style="flex:1" placeholder="min s">
        <input type="number" id="${p}BreakMax" min="0" value="300" style="flex:1" placeholder="max s">
    </div>
    <label>Max. captcha rounds <span class="tooltip" data-tip="How many times the study rotates/waits after captchas before it stops and asks for attention.">?</span></label>
    <input type="number" id="${p}MaxCaptcha" min="1" value="10">
    <hr style="border:0; border-top:1px solid #eee; margin:12px 0 0;">
    <label>Webhook URL (optional) <span class="tooltip" data-tip="Receives a JSON POST when the study finishes, needs attention (captcha, many empty pages) or fails. Works with Slack/Discord/ntfy style incoming webhooks.">?</span></label>
    <input type="text" id="${p}Webhook" placeholder="https://ntfy.sh/my-topic">
    <label>Repeat study <span class="tooltip" data-tip="After a run is finished, start a fresh copy of the study every X hours, Y times. The browser must stay open.">?</span></label>
    <div class="row">
        <input type="number" id="${p}RepeatHours" min="0" step="0.5" value="0" style="flex:1" placeholder="every X h">
        <input type="number" id="${p}RepeatTimes" min="0" value="0" style="flex:1" placeholder="Y times">
    </div>
    <div class="hint">0 = run once.</div>`;
}

function mountPanels() {
    [['createProxyMount', 'c', proxyPanelHtml], ['editProxyMount', 'e', proxyPanelHtml],
     ['createBehaviorMount', 'c', behaviorPanelHtml], ['editBehaviorMount', 'e', behaviorPanelHtml]].forEach(([id, p, fn]) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = fn(p);
    });
    ['c', 'e'].forEach(p => {
        const modeSel = document.getElementById(p + 'ProxyMode');
        modeSel.addEventListener('change', () => {
            document.getElementById(p + 'ProxyTplRow').style.display = modeSel.value === 'gateway' ? 'block' : 'none';
        });
        document.getElementById(p + 'ProxyTestBtn').addEventListener('click', () => runProxyTest(p));
    });
}

function readProxyOpts(p) {
    return {
        proxyMode: document.getElementById(p + 'ProxyMode').value,
        proxyUsernameTemplate: document.getElementById(p + 'ProxyTpl').value.trim(),
        proxyBudget: parseInt(document.getElementById(p + 'ProxyBudget').value, 10) || 0,
        proxyCooldownMin: parseInt(document.getElementById(p + 'ProxyCooldown').value, 10) || 120,
        clearCookiesOnRotate: document.getElementById(p + 'ProxyClearCookies').checked
    };
}

function readBehaviorOpts(p) {
    const num = (id, d) => { const v = parseInt(document.getElementById(p + id).value, 10); return isNaN(v) ? d : v; };
    return {
        behavior: {
            humanPacing: document.getElementById(p + 'HumanPacing').checked,
            trustedInput: document.getElementById(p + 'TrustedInput').checked,
            shuffle: document.getElementById(p + 'Shuffle').checked,
            typedSearch: document.getElementById(p + 'TypedSearch').checked,
            breakEvery: num('BreakEvery', 0),
            breakMinSec: num('BreakMin', 120),
            breakMaxSec: Math.max(num('BreakMax', 300), num('BreakMin', 120))
        },
        maxCaptchaRounds: Math.max(1, num('MaxCaptcha', 10)),
        webhookUrl: document.getElementById(p + 'Webhook').value.trim(),
        repeatEveryHours: parseFloat(document.getElementById(p + 'RepeatHours').value) || 0,
        repeatTimes: num('RepeatTimes', 0)
    };
}

function fillProxyOpts(p, st) {
    document.getElementById(p + 'ProxyMode').value = st.proxyMode === 'gateway' ? 'gateway' : 'list';
    document.getElementById(p + 'ProxyTpl').value = st.proxyUsernameTemplate || "";
    document.getElementById(p + 'ProxyBudget').value = st.proxyBudget || 0;
    document.getElementById(p + 'ProxyCooldown').value = st.proxyCooldownMin || 120;
    document.getElementById(p + 'ProxyClearCookies').checked = st.clearCookiesOnRotate !== false;
    document.getElementById(p + 'ProxyTplRow').style.display = st.proxyMode === 'gateway' ? 'block' : 'none';
}

function fillBehaviorOpts(p, st) {
    const b = st.behavior || {};
    document.getElementById(p + 'HumanPacing').checked = b.humanPacing !== false;
    document.getElementById(p + 'TrustedInput').checked = b.trustedInput !== false;
    document.getElementById(p + 'Shuffle').checked = !!b.shuffle;
    document.getElementById(p + 'TypedSearch').checked = !!b.typedSearch;
    document.getElementById(p + 'BreakEvery').value = b.breakEvery || 0;
    document.getElementById(p + 'BreakMin').value = b.breakMinSec !== undefined ? b.breakMinSec : 120;
    document.getElementById(p + 'BreakMax').value = b.breakMaxSec !== undefined ? b.breakMaxSec : 300;
    document.getElementById(p + 'MaxCaptcha').value = st.maxCaptchaRounds || 10;
    document.getElementById(p + 'Webhook').value = st.webhookUrl || "";
    document.getElementById(p + 'RepeatHours').value = st.repeatEveryHours || 0;
    document.getElementById(p + 'RepeatTimes').value = st.repeatTimes || 0;
}

function resetPanelDefaults(p) {
    fillProxyOpts(p, {});
    fillBehaviorOpts(p, {});
}

function formatProxyErrors(v) {
    if (!v || !v.errors || v.errors.length === 0) return "";
    return v.errors.map(e => `• ${e.line} → ${e.error}`).join("\n");
}

async function runProxyTest(p) {
    const out = document.getElementById(p + 'ProxyTestOut');
    const btn = document.getElementById(p + 'ProxyTestBtn');
    const listStr = document.getElementById(p === 'c' ? 'proxyList' : 'editProxyList').value;
    if (!listStr.trim()) { out.innerHTML = `<span class="bad-text">Enter at least one proxy first.</span>`; return; }
    btn.disabled = true;
    out.innerHTML = "⏳ Testing… (up to 10 s per proxy)";
    const opts = readProxyOpts(p);
    const res = await new Promise(r => chrome.runtime.sendMessage({
        action: "TEST_PROXIES",
        payload: {
            sessionId: p === 'e' ? currentSessionId : null,
            proxyListStr: listStr,
            proxyMode: opts.proxyMode,
            proxyUsernameTemplate: opts.proxyUsernameTemplate,
            webhookUrl: document.getElementById(p + 'Webhook').value.trim()
        }
    }, r));
    btn.disabled = false;
    if (!res || res.error) { out.innerHTML = `<span class="bad-text">${esc(res && res.error || "No response from the extension.")}</span>`; return; }
    let html = res.results.map(r => r.ok
        ? `<div class="ok-text">✔ ${esc(r.target)} → ${esc(r.ip)} ${esc(r.country)} (${r.ms} ms)</div>`
        : `<div class="bad-text">✘ ${esc(r.target)} → ${esc(r.error)}</div>`).join("");
    (res.errors || []).forEach(e => { html += `<div class="bad-text">⚠ ${esc(e.line)} → ${esc(e.error)}</div>`; });
    if (!res.results.length && !(res.errors || []).length) html = `<span class="bad-text">No usable proxy lines found.</span>`;
    out.innerHTML = html;
}

mountPanels();

// --- 1. LOCAL DATABASE HELPERS FOR HEAVY LIFTING ---
async function initLocalDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 8);
        request.onsuccess = () => { dbLocal = request.result; resolve(); };
        request.onerror = () => reject("DB Error");
    });
}

async function localGetAllSessions() {
    return new Promise(r => {
        const tx = dbLocal.transaction(STORE_SESSIONS, "readonly");
        const req = tx.objectStore(STORE_SESSIONS).getAll();
        req.onsuccess = () => r(req.result);
    });
}

async function localGetSession(id) {
    return new Promise(r => {
        const tx = dbLocal.transaction(STORE_SESSIONS, "readonly");
        const req = tx.objectStore(STORE_SESSIONS).get(id);
        req.onsuccess = () => r(req.result);
    });
}

async function localGetLogs(id) {
    return new Promise(r => {
        const tx = dbLocal.transaction(STORE_LOGS, "readonly");
        const req = tx.objectStore(STORE_LOGS).getAll();
        req.onsuccess = () => r(req.result.filter(l => l.sessionId === id));
    });
}

async function localGetPageContent(sessionId, taskIdx, pageNum) {
    return new Promise(r => {
        const tx = dbLocal.transaction(STORE_RESULTS, "readonly");
        const req = tx.objectStore(STORE_RESULTS).get(`${sessionId}_${taskIdx}_${pageNum}`);
        req.onsuccess = () => r(req.result);
    });
}

// --- 2. HEAVY LIFTING FUNCTIONS (IMPORT / EXPORT SESSIONS) ---
async function performImport(file) {
    if (!dbLocal) await initLocalDB();
    
    const btn = document.getElementById('importBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Importing...!";
    btn.disabled = true;
    btn.style.backgroundColor = "#6c757d";

    try {
        const zip = await JSZip.loadAsync(file); 
        const metaStr = await zip.file("sessions_metadata.json").async("string");
        const sessions = JSON.parse(metaStr);
        
        const tx = dbLocal.transaction([STORE_SESSIONS, STORE_RESULTS], "readwrite");
        sessions.forEach(s => tx.objectStore(STORE_SESSIONS).put(s));
        
        const resFolder = zip.folder("results");
        if (resFolder) {
            const resFiles = resFolder.file(/.*\.json$/);
            for (const f of resFiles) {
                const content = JSON.parse(await f.async("string"));
                const key = f.name.replace("results/", "").replace(".json", "");
                tx.objectStore(STORE_RESULTS).put(content, key);
            }
        }
        
        await new Promise(r => tx.oncomplete = r);
        alert("Import successful!");
        chrome.runtime.sendMessage({ action: "GET_SESSIONS" }); 
    } catch(e) {
        alert("Import Error: " + e.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.backgroundColor = "";
    }
}

async function performFullBackup() {
    if (!dbLocal) await initLocalDB();
    
    const btn = document.getElementById('exportAllBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Backing up...!";
    btn.disabled = true;
    btn.style.backgroundColor = "#6c757d";

    try {
        const sessions = await localGetAllSessions();
        const zip = new JSZip();
        zip.file("sessions_metadata.json", JSON.stringify(sessions));
        const resFolder = zip.folder("results");

        for (const sess of sessions) {
            for (let tIdx = 0; tIdx < sess.tasks.length; tIdx++) {
                for (const pg of sess.tasks[tIdx].pages) {
                    const data = await localGetPageContent(sess.id, tIdx, pg.pageNumber);
                    if (data) {
                        resFolder.file(`${sess.id}_${tIdx}_${pg.pageNumber}.json`, JSON.stringify(data));
                    }
                }
            }
        }
        
        const blob = await zip.generateAsync({ type: "blob", compression: "STORE" });
        const downloadUrl = URL.createObjectURL(blob);
        chrome.downloads.download({ 
            url: downloadUrl, 
            filename: `RAT_FULL_BACKUP.zip`,
            saveAs: true 
        }, () => {
            setTimeout(() => URL.revokeObjectURL(downloadUrl), 10000);
            btn.innerHTML = originalText;
            btn.disabled = false;
            btn.style.backgroundColor = "";
        });
    } catch(e) {
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.backgroundColor = "";
        alert("Backup Error: " + e.message);
    }
}

// A design contains only keywords, engines and non-secret settings: no results, no proxy credentials, no webhook.
function sanitizeStudyDesign(src, newId) {
    const d = JSON.parse(JSON.stringify(src));
    if (newId) { d.id = newId; }
    d.status = "OPEN";
    d.currentIndex = 0;
    d.runNumber = 1;
    delete d.metrics;
    delete d.retryAt;
    delete d.nextRunAt;
    delete d.captchaTabId;
    delete d.captchaRounds;
    delete d.progress;
    d.tasks = (d.tasks || []).map(t => ({
        term: t.term, config: t.config,
        status: t.status === "CANCELLED" ? "CANCELLED" : "OPEN",
        pages: [], totalOrganic: 0, retryCount: 0
    }));
    d.settings = d.settings || {};
    d.settings.useProxies = false;
    d.settings.proxyList = [];
    d.settings.webhookUrl = "";
    return d;
}

async function performExportStudyDesign(sessionId) {
    if (!dbLocal) await initLocalDB();
    try {
        const tx = dbLocal.transaction(STORE_SESSIONS, "readonly");
        const store = tx.objectStore(STORE_SESSIONS);
        const request = store.get(sessionId);

        request.onsuccess = async () => {
            const sessionData = request.result;
            if (!sessionData) {
                alert("Study not found!");
                return;
            }

            const design = sanitizeStudyDesign(sessionData);

            const zip = new JSZip();
            zip.file("study_design.json", JSON.stringify(design, null, 2));

            const blob = await zip.generateAsync({ type: "blob" });
            const url = URL.createObjectURL(blob);
            
            chrome.downloads.download({
                url: url,
                filename: `rat_job_${sessionId}.zip`,
                saveAs: true
            });
        };
    } catch (e) {
        console.error("Error exporting study design:", e);
    }
}

document.getElementById('importDesignInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        performImportStudyDesign(file);
    }
});

async function performImportStudyDesign(file) {
    try {
        const zip = await JSZip.loadAsync(file);
        const configFile = zip.file("study_design.json");

        if (!configFile) {
            alert("Error: No 'study_design.json' found in the archive! Are you sure this is a Study Design file?");
            return;
        }

        const jsonString = await configFile.async("string");
        const raw = JSON.parse(jsonString);
        if (!raw || !Array.isArray(raw.tasks) || !raw.originalConfigs) {
            alert("Error: This file does not look like a valid study design.");
            return;
        }
        if (!dbLocal) await initLocalDB();
        const sessionData = sanitizeStudyDesign(raw, "sess_" + Date.now());
        sessionData.name = (raw.baseName || raw.name || "Imported study");

        const tx = dbLocal.transaction(STORE_SESSIONS, "readwrite");
        const store = tx.objectStore(STORE_SESSIONS);
        store.put(sessionData);

        tx.oncomplete = () => {
            alert("Study Design successfully imported!\n\nProxy credentials and webhook are never part of a design - add your own in the study's Advanced Settings.");
            chrome.runtime.sendMessage({ action: "REFRESH_SESSIONS" });
            document.getElementById('importDesignInput').value = "";
        };

        tx.onerror = (err) => {
            console.error("Database error during import:", err);
            alert("Error saving the study design to the local database.");
        };

    } catch (e) {
        console.error("Import Error:", e);
        alert("Error importing and extracting the design. Check the console for details.");
    }
}

async function performExportDataAsZip(sessionId) {
    if (!dbLocal) await initLocalDB();
    
    const btn = document.getElementById('downloadBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Generating...!";
    btn.disabled = true;
    btn.style.backgroundColor = "#6c757d";

    const exportOrganic = document.getElementById('exportOrganic')?.checked ?? true;
    const exportAds = document.getElementById('exportAds')?.checked ?? true;
    const exportImages = document.getElementById('exportImages')?.checked ?? true;
    const exportVideos = document.getElementById('exportVideos')?.checked ?? true;
    const exportAiOverview = document.getElementById('exportAiOverview')?.checked ?? true;
    const exportAiSources = document.getElementById('exportAiSources')?.checked ?? true;
    const exportAiSegments = document.getElementById('exportAiSegments')?.checked ?? true;

    try {
        const session = await localGetSession(sessionId);
        const logs = await localGetLogs(sessionId);
        const zip = new JSZip();
        const imgFolder = zip.folder("screenshots");
        const htmlFolder = zip.folder("html");

        if (logs) {
            zip.file("activity_log.txt", logs.map(l => `[${l.ts}] [${l.level || 'INFO'}] ${l.msg}`).join("\n"));
        }

        let csv = "\uFEFFquery,engine,country,lang,page,type,rank,title,url,snippet,image_url,ai_full_text,source_type\n";
        const esc = (t) => t ? `"${String(t).replace(/"/g, '""')}"` : '""';

        for (let tIdx = 0; tIdx < session.tasks.length; tIdx++) {
            const q = session.tasks[tIdx];
            if (!q.pages || q.pages.length === 0) continue;

            const engineName = q.config.engineName || "Unknown Engine";
            const langStr = q.config.langCode ? q.config.langCode : "Auto";
            const meta = `${esc(q.term)},${esc(engineName)},${esc(q.config.countryName)},${esc(langStr)}`;

            const engineSafe = engineName.replace(/[^a-zA-Z0-9]/g, '');
            const termSafe = q.term.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
            const countrySafe = (q.config.countryCode || "us").toUpperCase();
            const langSafe = langStr.toUpperCase();

            for (const p of q.pages) {
                const extra = await localGetPageContent(sessionId, tIdx, p.pageNumber);
                const baseFileName = `${engineSafe}_${countrySafe}_${langSafe}_${termSafe}_p${p.pageNumber}`;

                if (extra) {
                    if (extra.screenshot) {
                        imgFolder.file(`${baseFileName}.jpg`, extra.screenshot.split(',')[1], { base64: true });
                    }
                    if (extra.html) {
                        htmlFolder.file(`${baseFileName}.html`, extra.html);
                    }
                }

                if (p.results.ai_overview?.found) {
                    if (exportAiOverview) {
                        csv += `${meta},${p.pageNumber},ai_overview,1,"AI Overview",,,,${esc(p.results.ai_overview.text_full)},\n`;
                    }
                    
                    if (exportAiSources && p.results.ai_overview.sources) {
                        p.results.ai_overview.sources.forEach((src, idx) => {
                            let srcType = src.type || "carousel"; 
                            csv += `${meta},${p.pageNumber},ai_source,${idx + 1},${esc(src.title)},${esc(src.url)},,,,${esc(srcType)}\n`;
                        });
                    }

                    if (exportAiSegments && p.results.ai_overview.segments) {
                        p.results.ai_overview.segments.forEach((seg, idx) => {
                            let citedUrls = "";
                            if (seg.citations && p.results.ai_overview.sources) {
                                citedUrls = seg.citations.map(cId => {
                                    let source = p.results.ai_overview.sources.find(s => s.id === cId);
                                    return source ? source.url : "";
                                }).filter(u => u !== "").join(" | ");
                            }
                            
                            csv += `${meta},${p.pageNumber},ai_segment,${idx + 1},"AI Segment ${idx + 1}",${esc(citedUrls)},${esc(seg.text)},,,\n`;
                        });
                    }
                }

                // Organic Results
                if (exportOrganic && p.results.organic) {
                    p.results.organic.forEach(r => {
                        csv += `${meta},${p.pageNumber},organic,${r.rank},${esc(r.title)},${esc(r.url)},${esc(r.snippet)},${esc(r.imageUrl)},,\n`;
                    });
                }
                
                // Image Results
                if (exportImages && p.results.images) {
                    p.results.images.forEach(r => {
                        csv += `${meta},${p.pageNumber},image,${r.rank},${esc(r.title)},${esc(r.url)},${esc(r.snippet)},${esc(r.imageUrl)},,\n`;
                    });
                }

                // Video Results
                if (exportVideos && p.results.videos) {
                    p.results.videos.forEach(v => {
                        csv += `${meta},${p.pageNumber},video,${v.rank},${esc(v.title)},${esc(v.url)},${esc(v.snippet)},${esc(v.imageUrl)},,\n`;
                    });
                }

                // Ads Results
                if (exportAds && p.results.ads) {
                    p.results.ads.forEach(ad => {
                        csv += `${meta},${p.pageNumber},ad,${ad.rank},${esc(ad.title)},${esc(ad.url)},${esc(ad.snippet)},${esc(ad.imageUrl)},,\n`;
                    });
                }
            }
        }

        zip.file("rat_results.csv", csv);

        const blob = await zip.generateAsync({ type: "blob", compression: "STORE" });
        const downloadUrl = URL.createObjectURL(blob);
        chrome.downloads.download({
            url: downloadUrl,
            filename: `RAT_Export_${session.name.replace(/\W/g, '_')}.zip`,
            saveAs: true
        }, () => {
            setTimeout(() => URL.revokeObjectURL(downloadUrl), 10000);
            btn.innerHTML = originalText;
            btn.disabled = false;
            btn.style.backgroundColor = ""; 
        });

    } catch (err) {
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.backgroundColor = "";
        alert("Critical Error during Export: " + err.message);
    }
}


// --- 3. INITIALIZATION & EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    initLocalDB(); 

    // Zoom
    applyZoom(currentZoom);
    document.querySelectorAll('.zoom-in-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentZoom = Math.min(currentZoom + 0.1, 2.0); 
            applyZoom(currentZoom);
        });
    });
    document.querySelectorAll('.zoom-out-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentZoom = Math.max(currentZoom - 0.1, 0.8); 
            applyZoom(currentZoom);
        });
    });

    setupDragAndDropForKeywords('sessQueries');
    setupDragAndDropForKeywords('addQueryInput');

    // Navigation Bindings
    document.getElementById('createSessionBtn').addEventListener('click', () => { resetCreateForm(); showView('createView'); });
    document.getElementById('backBtn').addEventListener('click', () => showView('listView'));
    document.getElementById('backToListBtn').addEventListener('click', () => { 
        currentSessionId = null; 
        cachedTasks = []; 
        showView('listView'); 
        chrome.runtime.sendMessage({ action: "GET_SESSIONS" }); 
    });
    
    document.getElementById('manageEnginesBtn').addEventListener('click', () => { showView('engineView'); document.getElementById('engineEditView').style.display = 'none'; document.getElementById('engineListView').style.display = 'block'; });
    document.getElementById('backToMainFromEnginesBtn').addEventListener('click', () => showView('listView'));

	// --- UULE / LOCATION VISIBILITY HELPER ---
	function updateLocationVisibility(engineId, rowId, inputId) {
		const row = document.getElementById(rowId);
		const input = document.getElementById(inputId);
		if (!row || !input) return;

		const engineObj = availableEngines.find(eng => eng.engine.id === engineId);
		
		// Check if the engine requires UULE or has 'google' in the ID
		const isGoogle = engineObj 
			? Boolean(engineObj.request?.features?.requiresUuleEncoding || engineObj.engine?.id?.toLowerCase().includes('google'))
			: false;

		if (isGoogle) {
			row.style.display = 'flex'; // Your .row class uses display: flex
		} else {
			row.style.display = 'none';
			input.value = ''; // Clear the hidden input so it doesn't get sent by mistake
		}
	}


    // Dynamic Engine Selection Handlers
	document.getElementById('confEngineSelect').addEventListener('change', (e) => {
		populateDropdowns(e.target.value, 'confCountrySelect', 'confLangSelect');
		
		// Toggle UULE / Location field for Google only
		updateLocationVisibility(e.target.value, 'confLocRow', 'confLoc');

		const limitTypeSelect = document.getElementById('sessLimitType');
		const engineObj = availableEngines.find(eng => eng.engine.id === e.target.value);
		
		if (engineObj && engineObj.selectors && engineObj.selectors.pagination && engineObj.selectors.pagination.type === "infinite_scroll") {
			limitTypeSelect.value = 'RESULTS';
			document.getElementById('sessLimit').value = 10;
			limitTypeSelect.style.border = '2px solid #17a2b8'; 
			limitTypeSelect.title = "For infinite scroll (like YouTube), filtering by 'Results' instead of 'Pages' is highly recommended!";
			const warningDiv = document.getElementById('infiniteScrollWarning');
			if(warningDiv) warningDiv.style.display = 'block';
		} else {
			limitTypeSelect.style.border = '1px solid #ced4da';
			limitTypeSelect.title = "";
			const warningDiv = document.getElementById('infiniteScrollWarning');
			if(warningDiv) warningDiv.style.display = 'none';
		}
	});

	document.getElementById('editConfEngineSelect').addEventListener('change', (e) => {
		populateDropdowns(e.target.value, 'editConfCountrySelect', 'editConfLangSelect');
		// Toggle UULE / Location field for Google only
		updateLocationVisibility(e.target.value, 'editConfLocRow', 'editConfLoc');
	});
    // Engine Form Visibility
    document.getElementById('showEngineFormBtn').addEventListener('click', () => {
        document.getElementById('engineFormContainer').style.display = 'block';
        document.getElementById('showEngineFormBtn').style.display = 'none';
        if(availableEngines.length > 0) document.getElementById('confEngineSelect').dispatchEvent(new Event('change'));
    });

    document.getElementById('cancelConfigBtn').addEventListener('click', () => {
        document.getElementById('engineFormContainer').style.display = 'none';
        document.getElementById('showEngineFormBtn').style.display = 'block';
    });

    // Serp Limit
    document.getElementById('editSaveSerp').addEventListener('change', (e) => {
        const limitContainer = document.getElementById('editSerpLimitContainer');
        if (e.target.checked) {
            alert("⚠️ WARNING: Saving SERPs (Screenshots & HTML) consumes massive amounts of storage and can slow down the extension. Please ensure you set a reasonable limit!");
            limitContainer.style.display = 'block';
        } else {
            limitContainer.style.display = 'none';
        }
    });

    // Add Task Config to Session Build
    document.getElementById('addConfigBtn').addEventListener('click', () => {
        const engineId = document.getElementById('confEngineSelect').value;
        const countryCode = document.getElementById('confCountrySelect').value;
        const langCode = document.getElementById('confLangSelect').value;
        const location = document.getElementById('confLoc').value.trim();
        
        const engine = availableEngines.find(e => e.engine.id === engineId);
		if (engine && countryCode) {
            const countryData = engine.request.supportedCountries.find(c => c.code === countryCode);
            const isGoogle = engine.request?.features?.requiresUuleEncoding || engine.engine.id.toLowerCase().includes('google');
            const finalLocation = isGoogle ? location : "";
            
            // Format the location nicely (add pin and truncate long UULE strings)
            let displayLoc = finalLocation;
            if (displayLoc.startsWith("w+CAIQICI") && displayLoc.length > 20) {
                displayLoc = displayLoc.substring(0, 15) + "...";
            }
            const finalEngineName = displayLoc ? `${engine.engine.name} (📍 ${displayLoc})` : engine.engine.name;

            addConfig({
                engineId: engine.engine.id,
                engineName: finalEngineName, // <-- FIX: Now using finalEngineName!
                countryName: countryData.name,
                countryCode: countryData.code,
                domain: countryData.domain || "",
                langCode: langCode || "", 
                location: finalLocation
            });
            document.getElementById('engineFormContainer').style.display = 'none';
            document.getElementById('showEngineFormBtn').style.display = 'block';
            document.getElementById('confLoc').value = ""; 
        } else { alert("Please select a Country."); }
    });

    document.getElementById('useProxies').addEventListener('change', (e) => {
        document.getElementById('proxyList').disabled = !e.target.checked;
        document.getElementById('createProxyMount').style.display = e.target.checked ? 'block' : 'none';
    });
    document.getElementById('createProxyMount').style.display = 'none';

    // Create Session Submission
    document.getElementById('startScrapeBtn').addEventListener('click', () => {
        const name = document.getElementById('sessName').value.trim();
        const q = document.getElementById('sessQueries').value.split('\n').filter(x => x.trim());
        const useProxies = document.getElementById('useProxies').checked;
        const proxyListStr = document.getElementById('proxyList').value;
        const saveSerp = document.getElementById('saveSerp').checked;
        
        const serpLimit = document.getElementById('sessSerpLimit') ? parseInt(document.getElementById('sessSerpLimit').value) : 100;

        const errorDiv = document.getElementById('createErrorMsg');
        
        errorDiv.style.display = 'none'; 
        if (!name) { errorDiv.innerText = "⚠️ Please enter a Session Name."; errorDiv.style.display = 'block'; return; }
        if (q.length === 0) { errorDiv.innerText = "⚠️ Please enter at least one Search Query."; errorDiv.style.display = 'block'; return; }
        if (currentConfigs.length === 0) { errorDiv.innerText = "⚠️ Please add at least one Search Engine configuration."; errorDiv.style.display = 'block'; return; }

        if (useProxies && !proxyListStr.trim()) { errorDiv.innerText = "⚠️ Proxies are enabled but the list is empty."; errorDiv.style.display = 'block'; return; }
        const dMin = parseInt(document.getElementById('sessMin').value), dMax = parseInt(document.getElementById('sessMax').value);
        if (!(dMin >= 0) || !(dMax >= dMin)) { errorDiv.innerText = "⚠️ Delays: Max must be greater than or equal to Min."; errorDiv.style.display = 'block'; return; }

        if (name && q.length > 0 && currentConfigs.length > 0) {
            const beh = readBehaviorOpts('c');
            const payload = {
                name, queries: q, configs: currentConfigs,
                resultsLimit: parseInt(document.getElementById('sessLimit').value),
                limitType: document.getElementById('sessLimitType').value,
                delays: { min: dMin * 1000, max: dMax * 1000 },
                saveSerp,
                serpLimit,
                useProxies, proxyListStr,
                ...readProxyOpts('c'),
                ...beh
            };
            chrome.runtime.sendMessage({ action: "CREATE_SESSION", payload }, (res) => {
                void chrome.runtime.lastError;
                const msg = formatProxyErrors(res && res.proxy);
                if (msg) alert("Some proxy lines were ignored:\n\n" + msg);
            });
        }
    });

    document.getElementById('playPauseBtn').addEventListener('click', () => {
        const btn = document.getElementById('playPauseBtn');
        if (btn.innerText === "Pause") chrome.runtime.sendMessage({ action: "PAUSE", payload: { sessionId: currentSessionId } });
        else chrome.runtime.sendMessage({ action: "START", payload: { sessionId: currentSessionId } });
    });

    document.getElementById('stopBtn').addEventListener('click', () => { 
        if (confirm("Delete session?")) { 
            chrome.runtime.sendMessage({ action: "DELETE_SESSION", payload: { sessionId: currentSessionId } }); 
            showView('listView'); 
        } 
    });

// --- DIRECT IMPORT/EXPORT BINDS ---
    document.getElementById('exportDesignBtn').addEventListener('click', () => {
        if(currentSessionId) performExportStudyDesign(currentSessionId);
    });

    document.getElementById('downloadBtn').addEventListener('click', () => {
        if(currentSessionId) performExportDataAsZip(currentSessionId);
    });
    
    document.getElementById('exportAllBtn').addEventListener('click', () => { performFullBackup(); });
    document.getElementById('importBtn').addEventListener('click', () => document.getElementById('importFile').click());
    
    document.getElementById('importFile').addEventListener('change', (e) => {
        const f = e.target.files[0];
        if (f && f.name.endsWith('.zip')) performImport(f);
        e.target.value = '';
    });
    
    // --- LIVE CONTROLS ---
    document.getElementById('applyDelayBtn').addEventListener('click', () => {
        const min = parseInt(document.getElementById('liveMin').value);
        const max = parseInt(document.getElementById('liveMax').value);
        if(currentSessionId && min && max) chrome.runtime.sendMessage({ action: "UPDATE_DELAY", payload: { sessionId: currentSessionId, min, max }});
    });

	document.getElementById('applyLimitBtn').addEventListener('click', () => {
        const limit = parseInt(document.getElementById('liveLimit').value);
        const limitType = document.getElementById('liveLimitType').value;
        if(currentSessionId && limit) {
            chrome.runtime.sendMessage({ action: "UPDATE_LIMIT", payload: { sessionId: currentSessionId, limit: limit, limitType: limitType }});
            alert(`Target Quota updated to ${limit} ${limitType.toLowerCase()}.`);
        }
    });

    document.getElementById('showEditEngineFormBtn').addEventListener('click', () => {
        document.getElementById('editEngineFormContainer').style.display = 'block';
        document.getElementById('showEditEngineFormBtn').style.display = 'none';
        if(availableEngines.length > 0) document.getElementById('editConfEngineSelect').dispatchEvent(new Event('change'));
    });

    document.getElementById('cancelEditConfigBtn').addEventListener('click', () => {
        document.getElementById('editEngineFormContainer').style.display = 'none';
        document.getElementById('showEditEngineFormBtn').style.display = 'block';
    });

    document.getElementById('submitNewQueries').addEventListener('click', () => {
        const txt = document.getElementById('addQueryInput').value;
        const queries = txt.split('\n').filter(x => x.trim());
        const errorDiv = document.getElementById('addQueryErrorMsg');
        errorDiv.style.display = 'none'; 

        if (queries.length === 0) { errorDiv.innerText = "⚠️ Please enter at least one keyword to add."; errorDiv.style.display = 'block'; return; }
        if(queries.length > 0 && currentSessionId) {
            chrome.runtime.sendMessage({ action: "ADD_ITEMS", payload: { sessionId: currentSessionId, newQueries: queries } });
            document.getElementById('addQueryInput').value = "";
            alert(`Added ${queries.length} queries to queue.`);
        }
    });

    document.getElementById('submitNewEngine').addEventListener('click', () => {
        const engineId = document.getElementById('editConfEngineSelect').value;
        const countryCode = document.getElementById('editConfCountrySelect').value;
        const langCode = document.getElementById('editConfLangSelect').value;
        const location = document.getElementById('editConfLoc').value.trim();
        const errorDiv = document.getElementById('addEngineErrorMsg');
        
        errorDiv.style.display = 'none';
        if (!countryCode) { errorDiv.innerText = "⚠️ Please select a Country to configure the search engine."; errorDiv.style.display = 'block'; return; }

		if (countryCode && currentSessionId) {
            const engine = availableEngines.find(e => e.engine.id === engineId);
            const countryData = engine.request.supportedCountries.find(c => c.code === countryCode);
            
            const isGoogle = engine.request?.features?.requiresUuleEncoding || engine.engine.id.toLowerCase().includes('google');
            const finalLocation = isGoogle ? location : "";
            
            // Format the location nicely
            let displayLoc = finalLocation;
            if (displayLoc.startsWith("w+CAIQICI") && displayLoc.length > 20) {
                displayLoc = displayLoc.substring(0, 15) + "...";
            }
            const finalEngineName = displayLoc ? `${engine.engine.name} (📍 ${displayLoc})` : engine.engine.name;
            
            const newConfig = {
                engineId: engine.engine.id,
                engineName: finalEngineName, 
                countryName: countryData.name,
                countryCode: countryData.code, 
                domain: countryData.domain || "",
                langCode: langCode || "", 
                location: finalLocation
            };
            
            if(confirm(`Add ${engine.engine.name} ${countryData.name} and generate tasks for ALL existing keywords?`)) {
                chrome.runtime.sendMessage({ action: "ADD_ITEMS", payload: { sessionId: currentSessionId, newConfigs: [newConfig] } });
                document.getElementById('editEngineFormContainer').style.display = 'none';
                document.getElementById('showEditEngineFormBtn').style.display = 'block';
                document.getElementById('editConfLoc').value = "";
            }
        }
    });

    document.getElementById('saveProxySettings').addEventListener('click', () => {
        const useProxies = document.getElementById('editUseProxies').checked;
        const proxyListStr = document.getElementById('editProxyList').value;
        if(currentSessionId) {
            chrome.runtime.sendMessage({ action: "UPDATE_PROXIES", payload: { sessionId: currentSessionId, useProxies, proxyListStr, ...readProxyOpts('e') } }, (res) => {
                void chrome.runtime.lastError;
                if (!res || res.error) { alert("Could not update proxies: " + (res && res.error || "no response")); return; }
                const msg = formatProxyErrors(res);
                alert(useProxies
                    ? `Proxy settings updated. ${res.valid} usable ${res.valid === 1 ? "entry" : "entries"}.` + (msg ? "\n\nIgnored lines:\n" + msg : "")
                    : "Proxies disabled.");
                panelsFilledFor = null;
            });
        }
    });

    document.getElementById('saveBehaviorBtn').addEventListener('click', () => {
        if (!currentSessionId) return;
        chrome.runtime.sendMessage({ action: "UPDATE_BEHAVIOR", payload: { sessionId: currentSessionId, ...readBehaviorOpts('e') } }, (res) => {
            void chrome.runtime.lastError;
            if (!res || res.error) { alert("Could not update: " + (res && res.error || "no response")); return; }
            alert("Behavior settings updated." + (res.warning ? "\n\n⚠️ " + res.warning : ""));
            panelsFilledFor = null;
        });
    });

    document.getElementById('saveStorageSettingsBtn').addEventListener('click', () => {
        const saveSerp = document.getElementById('editSaveSerp').checked;
        const serpLimit = document.getElementById('editSessSerpLimit') ? parseInt(document.getElementById('editSessSerpLimit').value) : 100;
        
        if(currentSessionId) {
            chrome.runtime.sendMessage({ 
                action: "UPDATE_STORAGE_SETTINGS", 
                payload: { sessionId: currentSessionId, saveSerp, serpLimit } 
            });
            alert("Storage settings updated.");
        }
    });


    document.getElementById('saveSerp').addEventListener('change', (e) => {
        const limitContainer = document.getElementById('serpLimitContainer');
        if (e.target.checked) {
            alert("⚠️ WARNING: Saving SERPs (Screenshots & HTML) consumes massive amounts of storage and can slow down the extension. Please ensure you set a reasonable limit!");
            limitContainer.style.display = 'block';
        } else {
            limitContainer.style.display = 'none';
        }
    });


    document.getElementById('refreshTasksBtn').addEventListener('click', () => {
        if(currentSessionId) {
            document.getElementById('taskListContainer').innerHTML = "<div style='padding:10px;text-align:center'>Loading...</div>";
            chrome.runtime.sendMessage({ action: "GET_TASKS", payload: { sessionId: currentSessionId } });
        }
    });

    const taskContainer = document.getElementById('taskListContainer');
    taskContainer.addEventListener('click', (e) => {
        const target = e.target;
        const action = target.dataset.action; 
        const index = parseInt(target.dataset.index);

        if (action === 'retry') retryTask(index);
        else if (action === 'delete') deleteTask(index);
        else if (action === 'prev') changeTaskPage(-1);
        else if (action === 'next') changeTaskPage(1);
    });

    document.getElementById('queriesAndTasksDetails').addEventListener('toggle', (e) => {
        if (e.target.open && currentSessionId) {
            chrome.runtime.sendMessage({ action: "GET_TASKS", payload: { sessionId: currentSessionId } });
        }
    });

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentTaskFilter = e.target.getAttribute('data-filter');
            currentTaskPage = 1; 
            renderTasks();
        });
    });

    // TWO-WAY BINDING: JSON -> Visual Builder
    function updateVisualBuilderFromJson() {
        try {
            const j = JSON.parse(document.getElementById('engineJsonEditor').value);
            document.getElementById('vbEngineName').value = j.engine?.name || "";
            document.getElementById('vbEngineId').value = j.engine?.id || "";
            document.getElementById('vbBaseUrl').value = j.request?.baseUrl || "";
            document.getElementById('vbParamQuery').value = j.request?.params?.query || "";
            
            const mainTarget = j.selectors?.images || j.selectors?.organic || {};
            
            document.getElementById('vbSelContainer').value = mainTarget.container || "";
            document.getElementById('vbSelTitle').value = mainTarget.title || "";
            document.getElementById('vbSelUrl').value = mainTarget.url || "";
            
            let snippetSel = mainTarget.snippet;
            document.getElementById('vbSelSnippet').value = (typeof snippetSel === 'object' && snippetSel !== null) ? (snippetSel.selector || "") : (snippetSel || "");
            
            document.getElementById('vbSelNext').value = j.selectors?.pagination?.nextButton || "";

            document.getElementById('vbSelAdContainer').value = j.selectors?.ads?.container || "";
            document.getElementById('vbSelAdTitle').value = j.selectors?.ads?.title || "";
            document.getElementById('vbSelAdUrl').value = j.selectors?.ads?.url || "";
            
            let adSnippetSel = j.selectors?.ads?.snippet;
            document.getElementById('vbSelAdSnippet').value = (typeof adSnippetSel === 'object' && adSnippetSel !== null) ? (adSnippetSel.selector || "") : (adSnippetSel || "");

            document.getElementById('vbSelAiContainer').value = j.selectors?.ai_overview?.container || "";
            document.getElementById('vbSelAiText').value = j.selectors?.ai_overview?.text?.selector || "";
            
            let aiSources = j.selectors?.ai_overview?.sources;
            if (Array.isArray(aiSources) && aiSources.length > 0) {
                const src = aiSources.find(s => s.type !== "attribute_based") || aiSources[0];
                document.getElementById('vbSelAiSourceContainer').value = src.container || "";
                document.getElementById('vbSelAiSourceTitle').value = src.title || "";
                document.getElementById('vbSelAiSourceUrl').value = src.url || "";
            } else {
                document.getElementById('vbSelAiSourceContainer').value = "";
                document.getElementById('vbSelAiSourceTitle').value = "";
                document.getElementById('vbSelAiSourceUrl').value = "";
            }
        } catch(e) { }
    }

    // TWO-WAY BINDING: Visual Builder -> JSON
    function updateJsonFromVisualBuilder() {
        try {
            let j = JSON.parse(document.getElementById('engineJsonEditor').value);
            
            j.engine = j.engine || {};
            j.engine.name = document.getElementById('vbEngineName').value;
            j.engine.id = document.getElementById('vbEngineId').value;
            
            j.request = j.request || {};
            j.request.baseUrl = document.getElementById('vbBaseUrl').value;
            j.request.params = j.request.params || {};
            j.request.params.query = document.getElementById('vbParamQuery').value;
            
            j.selectors = j.selectors || {};
            
            let isImageEngine = !!j.selectors.images;
            let mainTarget = isImageEngine ? j.selectors.images : (j.selectors.organic || {});
            
            mainTarget.container = document.getElementById('vbSelContainer').value;
            mainTarget.title = document.getElementById('vbSelTitle').value;
            mainTarget.url = document.getElementById('vbSelUrl').value;
            let snippetVal = document.getElementById('vbSelSnippet').value;
            
            if (typeof mainTarget.snippet === 'object' && mainTarget.snippet !== null) {
                mainTarget.snippet.selector = snippetVal;
            } else { 
                mainTarget.snippet = snippetVal; 
            }

            if (isImageEngine) {
                j.selectors.images = mainTarget;
            } else {
                j.selectors.organic = mainTarget;
            }
            
            j.selectors.pagination = j.selectors.pagination || {};
            j.selectors.pagination.nextButton = document.getElementById('vbSelNext').value;

            j.selectors.ads = j.selectors.ads || {};
            j.selectors.ads.container = document.getElementById('vbSelAdContainer').value || null;
            j.selectors.ads.title = document.getElementById('vbSelAdTitle').value || null;
            j.selectors.ads.url = document.getElementById('vbSelAdUrl').value || null;
            let adSnippetVal = document.getElementById('vbSelAdSnippet').value;
            
            if (typeof j.selectors.ads.snippet === 'object' && j.selectors.ads.snippet !== null) {
                j.selectors.ads.snippet.selector = adSnippetVal || null;
            } else { 
                j.selectors.ads.snippet = adSnippetVal || null; 
            }

            let aiCont = document.getElementById('vbSelAiContainer').value;
            let aiText = document.getElementById('vbSelAiText').value;
            let aiSrcCont = document.getElementById('vbSelAiSourceContainer').value;
            let srcTitle = document.getElementById('vbSelAiSourceTitle').value;
            let srcUrl = document.getElementById('vbSelAiSourceUrl').value;

            j.selectors.ai_overview = j.selectors.ai_overview || {};
            j.selectors.ai_overview.container = aiCont || null;
            
            j.selectors.ai_overview.text = j.selectors.ai_overview.text || {};
            j.selectors.ai_overview.text.selector = aiText || null;

            if (aiSrcCont) {
                j.selectors.ai_overview.sources = [{
                    type: "standard",
                    container: aiSrcCont,
                    title: srcTitle || null,
                    url: srcUrl || null
                }];
            } else if (!j.selectors.ai_overview.sources) {
                j.selectors.ai_overview.sources = null;
            }
            
            document.getElementById('engineJsonEditor').value = JSON.stringify(j, null, 2);
        } catch(e) { }
    }

    const vbInputs = [
        'vbEngineName', 'vbEngineId', 'vbBaseUrl', 'vbParamQuery', 
        'vbSelContainer', 'vbSelTitle', 'vbSelUrl', 'vbSelSnippet', 'vbSelNext',
        'vbSelAdContainer', 'vbSelAdTitle', 'vbSelAdUrl', 'vbSelAdSnippet',
        'vbSelAiContainer', 'vbSelAiText', 'vbSelAiSourceContainer', 'vbSelAiSourceTitle', 'vbSelAiSourceUrl'
    ];
    
    vbInputs.forEach(id => {
        const el = document.getElementById(id);
        if(el) el.addEventListener('input', updateJsonFromVisualBuilder);
    });

    document.getElementById('engineJsonEditor').addEventListener('input', updateVisualBuilderFromJson);

    // IMPORT JSON LOGIC
    document.getElementById('importEngineBtn').addEventListener('click', () => {
        document.getElementById('importEngineFile').click();
    });

    document.getElementById('importEngineFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const parsed = JSON.parse(event.target.result);
                if (!parsed.engine || !parsed.engine.id) throw new Error("Missing engine.id. This is not a valid RAT Plugin.");
                if (!parsed.request || !parsed.request.baseUrl) throw new Error("Missing request.baseUrl.");
                
                chrome.runtime.sendMessage({ action: "SAVE_ENGINE", payload: parsed });
                alert(`Plugin '${parsed.engine.name}' imported successfully!`);
            } catch(err) {
                alert("Import failed: " + err.message);
            }
            e.target.value = ''; 
        };
        reader.readAsText(file);
    });

    // EXPORT JSON LOGIC
    document.getElementById('exportEngineBtn').addEventListener('click', () => {
        try {
            const j = JSON.parse(document.getElementById('engineJsonEditor').value);
            const blob = new Blob([JSON.stringify(j, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            
            chrome.downloads.download({
                url: url,
                filename: `${j.engine.id || 'rat_scraper'}.json`,
                saveAs: true
            }, () => {
                setTimeout(() => URL.revokeObjectURL(url), 10000);
            });
        } catch (e) {
            alert("Cannot export: The JSON configuration contains errors.");
        }
    });

    document.getElementById('addNewEngineBtn').addEventListener('click', () => {
        currentEditingEngineId = null;
		document.getElementById('engineJsonEditor').value = `{\n  "manifest_version": 1,\n  "engine": {\n    "id": "new_scraper",\n    "name": "My Custom Engine"\n  },\n  "request": {\n    "baseUrl": "https://{domain}/search",\n    "params": {\n      "query": "q",\n      "country": "gl",\n      "language": "hl"\n    },\n    "features": { "requiresUuleEncoding": false, "urlDecodingMethod": "none" },\n    "supportedCountries": [\n      { "code": "us", "name": "USA", "domain": "www.example.com" }\n    ],\n    "supportedLanguages": [\n      { "code": "en", "name": "English" }\n    ]\n  },\n  "behavior": {},\n  "captcha": {},\n  "selectors": {\n    "pagination": { "nextButton": ".next" },\n    "organic": {\n      "container": ".result",\n      "title": "h2",\n      "url": "a",\n      "snippet": { "selector": ".snippet" }\n    },\n    "ads": { "container": ".ad", "title": "h2", "url": "a", "snippet": { "selector": ".snippet" } },\n    "videos": { "container": null, "title": null, "url": null, "channel": null, "duration": null, "date": null, "image": null },\n    "ai_overview": { "container": null, "text": null, "inline_citations": { "selector": null }, "sources": null }\n  }\n}`;
				
        document.getElementById('engineListView').style.display = 'none';
        document.getElementById('engineEditView').style.display = 'block';
        resetSandboxUI();
        populateSandboxDropdowns(JSON.parse(document.getElementById('engineJsonEditor').value));
        
        document.getElementById('deleteEngineBtn').style.display = 'none'; 
    });

    document.getElementById('cancelEngineEditBtn').addEventListener('click', () => {
        document.getElementById('engineEditView').style.display = 'none';
        document.getElementById('engineListView').style.display = 'block';
    });

    document.getElementById('deleteEngineBtn').addEventListener('click', () => {
        if (!currentEditingEngineId) return;
        
        const confirmMsg = "Are you sure you want to delete this scraper permanently? This action cannot be undone.";
        
        if (confirm(confirmMsg)) {
            chrome.runtime.sendMessage({ action: "DELETE_ENGINE", payload: { id: currentEditingEngineId } });
            
            document.getElementById('engineEditView').style.display = 'none';
            document.getElementById('engineListView').style.display = 'block';
        }
    });

    document.getElementById('saveEngineJsonBtn').addEventListener('click', () => {
        const errorDiv = document.getElementById('engineJsonError');
        errorDiv.style.display = 'none';
        try {
            const parsed = JSON.parse(document.getElementById('engineJsonEditor').value);
            if (!parsed.engine || !parsed.engine.id) throw new Error("Missing engine.id in JSON");
            if (!parsed.request || !parsed.request.baseUrl) throw new Error("Missing request.baseUrl in JSON");
            
            chrome.runtime.sendMessage({ action: "SAVE_ENGINE", payload: parsed });
            alert("Plugin saved successfully!");
            document.getElementById('engineEditView').style.display = 'none';
            document.getElementById('engineListView').style.display = 'block';
        } catch(e) {
            errorDiv.innerText = "JSON Error: " + e.message;
            errorDiv.style.display = 'block';
        }
    });

    document.getElementById('resetEngineBtn').addEventListener('click', async () => {
        if (!currentEditingEngineId) return;
        if (confirm("Reset this engine to its factory default? All custom changes will be lost.")) {
            try {
                const res = await fetch(chrome.runtime.getURL(`engines/${currentEditingEngineId}.json`));
                const originalJson = await res.json();
                chrome.runtime.sendMessage({ action: "SAVE_ENGINE", payload: originalJson });
                alert("Reset successful.");
                document.getElementById('engineEditView').style.display = 'none';
                document.getElementById('engineListView').style.display = 'block';
            } catch(e) {
                alert("Could not find default file for this engine in /engines/ folder.");
            }
        }
    });

    function logToSandbox(msg, color = "#333") {
        const div = document.getElementById('sandboxLiveLog');
        div.innerHTML += `<div style="border-bottom:1px solid #eee;padding:2px 0; color:${color}">
            <span style="color:#999;margin-right:5px;font-size:10px">[${new Date().toLocaleTimeString()}]</span>${msg}
        </div>`;
        div.scrollTop = div.scrollHeight;
    }

    function resetSandboxUI() {
        document.getElementById('sandboxLiveLog').innerHTML = "Waiting to start test...";
        document.getElementById('sandboxResultsPreview').innerHTML = "";
        document.getElementById('sandboxResultsPreview').style.display = 'none';
        document.getElementById('sandboxPreviewLabel').style.display = 'none';
    }

    document.getElementById('runSandboxBtn').addEventListener('click', async () => {
        document.getElementById('sandboxLiveLog').innerHTML = "";
        document.getElementById('sandboxResultsPreview').style.display = 'none';
        document.getElementById('sandboxPreviewLabel').style.display = 'none';
        
        logToSandbox("🚀 Starting sandbox isolation...", "#004085");
        
        try {
            const engineConfig = JSON.parse(document.getElementById('engineJsonEditor').value);
            const query = document.getElementById('sandboxQuery').value.trim() || "what is climate change?";
            const countryCode = document.getElementById('sandboxCountry').value;
            const langCode = document.getElementById('sandboxLanguage').value;

            const reqData = engineConfig.request;
            const countryData = reqData.supportedCountries.find(c => c.code === countryCode) || reqData.supportedCountries[0];
            let u = reqData.baseUrl.replace("{domain}", countryData.domain || "");
            const urlObj = new URL(u);
            if (reqData.params.query) urlObj.searchParams.set(reqData.params.query, query);
            if (reqData.params.country && countryCode) urlObj.searchParams.set(reqData.params.country, countryCode);
            if (reqData.params.language && langCode) urlObj.searchParams.set(reqData.params.language, langCode);
            const finalUrl = urlObj.toString();

            logToSandbox(`🔗 Opening Tab: ${finalUrl}`);
            
            const tab = await new Promise(r => chrome.tabs.create({ url: finalUrl, active: true }, r));
            
            logToSandbox(`⏳ Waiting for page to load completely...`);
            await new Promise(r => {
                const l = (id, chg) => {
                    if (id === tab.id && chg.status === 'complete') {
                        chrome.tabs.onUpdated.removeListener(l);
                        r();
                    }
                };
                chrome.tabs.onUpdated.addListener(l);
            });

            await new Promise(r => setTimeout(r, 2000));
            logToSandbox(`💉 Injecting content scripts and engine rules...`);
            await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });

            let collectedOrganic = [];
            let collectedAds = [];
            let aiOverviewData = null;
            let currentPage = 1;
            const targetResults = 20; 
            const existingUrls = new Set();
            
            while (collectedOrganic.length < targetResults && currentPage <= 5) {
                await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] }).catch(() => {});
                
                logToSandbox(`📜 Page ${currentPage}: Executing human logic & scrolling...`);
                await chrome.tabs.sendMessage(tab.id, { action: "SCROLL_AND_PREPARE", payload: { config: engineConfig } }).catch(()=>{});
                
                await new Promise(r => setTimeout(r, 2500));
                
                logToSandbox(`🔍 Page ${currentPage}: Extracting Data using JSON selectors...`);
                const response = await chrome.tabs.sendMessage(tab.id, { action: "SCRAPE_SERP", payload: { startRank: collectedOrganic.length, config: engineConfig } }).catch(() => null);

                if (response && response.data) {
                    const data = response.data;
                    
                    const newOrganic = (data.organic || []).filter(r => !existingUrls.has(r.url));
                    const newImages = (data.images || []).filter(r => !existingUrls.has(r.url));
                    const newVideos = (data.videos || []).filter(r => !existingUrls.has(r.url));
                    
                    newOrganic.forEach(r => existingUrls.add(r.url));
                    newImages.forEach(r => existingUrls.add(r.url));
                    newVideos.forEach(r => existingUrls.add(r.url));
                    
                    collectedOrganic = collectedOrganic.concat(newOrganic).concat(newImages).concat(newVideos);
                    collectedAds = collectedAds.concat(data.ads || []);
                    
                    if (data.ai_overview && data.ai_overview.found) {
                        if (!aiOverviewData) aiOverviewData = data.ai_overview; 
                        const sourceCount = data.ai_overview.sources ? data.ai_overview.sources.length : 0;
                        logToSandbox(`🤖 AI Overview / Search Assist successfully extracted! (${sourceCount} sources found)`, "#17a2b8");
                    }

                    if (data.ads && data.ads.length > 0) {
                        logToSandbox(`📢 Extracted ${data.ads.length} Ad(s) on Page ${currentPage}.`, "#fd7e14");
                    }

                    const aiFoundStr = (data.ai_overview && data.ai_overview.found) ? "Yes" : "No";
                    const aiSegs = (data.ai_overview && data.ai_overview.segments) ? data.ai_overview.segments.length : 0;
                    const totalNew = newOrganic.length + newImages.length + newVideos.length;
                    
                    logToSandbox(`📊 Page ${currentPage} Summary: AI: ${aiFoundStr} (${aiSegs} Segs) | Ads: ${data.ads.length} | Img: ${newImages.length} | Vid: ${newVideos.length} | Org: ${newOrganic.length} | New: ${totalNew} (Total: ${collectedOrganic.length}/${targetResults})`);

                    if (totalNew > 0) {
                        const firstRes = newOrganic.length > 0 ? newOrganic[0] : (newVideos.length > 0 ? newVideos[0] : newImages[0]);
                        const shortSnippet = firstRes.snippet ? firstRes.snippet.substring(0, 60).replace(/\n/g, ' ') + "..." : "No snippet found";
                        logToSandbox(`📝 Preview Rank ${collectedOrganic.length - totalNew + 1}: "${firstRes.title.substring(0,30)}..." - ${shortSnippet}`, "#555");
                    }

                    if (collectedOrganic.length >= targetResults) {
                        logToSandbox(`🎯 Target of ${targetResults} results reached!`, "#155724");
                        break;
                    }

                    logToSandbox(`⏭️ Attempting to click "Next/More" button...`);
                    const nav = await chrome.tabs.sendMessage(tab.id, { action: "NAVIGATE_NEXT", payload: { config: engineConfig } });

                    if (nav && nav.success) {
                        logToSandbox(`✅ Successfully clicked "Next/More". Moving to Page ${currentPage + 1}...`, "#155724");
                        currentPage++;
                        await new Promise(r => setTimeout(r, 4500)); 
                    } else {
                        logToSandbox(`⏹️ END: No "Next/More" button found or it failed. Stopping here.`, "#856404");
                        break;
                    }

                } else if (response && response.isCaptcha) {
                    logToSandbox(`❌ BLOCKED: CAPTCHA detected by engine rules!`, "#721c24");
                    break;
                } else {
                    logToSandbox(`❌ FAILED: Content script did not return data. Check CSS selectors.`, "#721c24");
                    break;
                }
            }

            const previewDiv = document.getElementById('sandboxResultsPreview');
            let html = "";
            
            if (aiOverviewData) {
                html += `<div class="sandbox-card" style="border-color:#17a2b8; background:#e0f7fa;">
                    <div class="sandbox-card-title">🤖 AI Overview Detected</div>
                    <div class="sandbox-card-snippet">
                        <strong>Text Preview:</strong><br>
                        <pre style="white-space: pre-wrap; word-break: break-all; font-family: monospace; font-size: 10px; background: #fff; padding: 5px;">${aiOverviewData.text_full}</pre>
                    </div>
                    <div style="font-size:10px; color:#666; margin-top:5px;">Sources found: ${aiOverviewData.sources.length}</div>
                    <div style="font-size:10px; color:#666;">
                        ${aiOverviewData.sources.map(s => `<div>🔗 ${s.title}: <a href="${s.url}" target="_blank">${s.url.substring(0,40)}...</a></div>`).join('')}
                    </div>
                </div>`;
            }

            collectedOrganic.slice(0, targetResults).forEach((res, idx) => {
                html += `<div class="sandbox-card">
                    <div style="font-size:10px; color:#888;">Rank ${idx + 1}</div>
                    <div class="sandbox-card-title">${res.title}</div>
                    <div class="sandbox-card-url">${res.url}</div>
                    <div class="sandbox-card-snippet">${res.snippet}</div>
                    ${res.imageUrl ? `<img src="${res.imageUrl}" style="max-width:100%; margin-top:8px; border-radius:4px; border:1px solid #eee;">` : ''}
                </div>`;
            });

            previewDiv.innerHTML = html;
            previewDiv.style.display = 'block';
            document.getElementById('sandboxPreviewLabel').style.display = 'block';
            
            chrome.tabs.remove(tab.id).catch(()=>{});

        } catch(err) {
            logToSandbox(`❌ CRITICAL ERROR: ${err.message}`, "#721c24");
        }
    });

    chrome.runtime.sendMessage({ action: "GET_SESSIONS" });
    chrome.runtime.sendMessage({ action: "GET_ENGINES" });
});

// --- 4. MESSAGE HANDLERS ---
chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "SESSION_LIST") renderList(msg.payload);
    if (msg.type === "SESSION_STATUS") updateStatus(msg.payload);
    if (msg.type === "LOG_ENTRY" && msg.payload.sessionId === currentSessionId) addSingleLog(msg.payload.entry);
    if (msg.type === "ENGINE_LIST") {
        availableEngines = msg.payload;
        populateEngineSelects();
        renderEngineList(msg.payload);
    }
    
    if (msg.type === "SESSION_CREATED") { 
        if (msg.payload && msg.payload.sessionId) openSession(msg.payload.sessionId);
        else { showView('listView'); chrome.runtime.sendMessage({ action: "GET_SESSIONS" }); }
    }
    
    if (msg.type === "TASK_LIST_UPDATE" && msg.payload.sessionId === currentSessionId) {
        cachedTasks = msg.payload.tasks;
        renderTasks();
    }
});

// --- 5. UI RENDERING FUNCTIONS ---

function populateEngineSelects() {
    const createsel = document.getElementById('confEngineSelect');
    const editsel = document.getElementById('editConfEngineSelect');
    createsel.innerHTML = ""; editsel.innerHTML = "";
    
    availableEngines.forEach(e => {
        const opt1 = document.createElement('option'); opt1.value = e.engine.id; opt1.innerText = e.engine.name; createsel.appendChild(opt1);
        const opt2 = document.createElement('option'); opt2.value = e.engine.id; opt2.innerText = e.engine.name; editsel.appendChild(opt2);
    });
    
    if (availableEngines.length > 0) {
        createsel.dispatchEvent(new Event('change'));
        editsel.dispatchEvent(new Event('change'));
    }
}

function populateDropdowns(engineId, countrySelectId, langSelectId) {
    const engine = availableEngines.find(e => e.engine.id === engineId);
    if (!engine) return;

    const cSelect = document.getElementById(countrySelectId);
    const lSelect = document.getElementById(langSelectId);
    cSelect.innerHTML = `<option value="" disabled selected>Select Country</option>`;
    lSelect.innerHTML = `<option value="" disabled selected>Select Language</option>`;

    if(engine.request.supportedCountries) {
        engine.request.supportedCountries.sort((a,b) => a.name.localeCompare(b.name)).forEach(c => {
            const opt = document.createElement('option'); opt.value = c.code; opt.innerText = c.name; cSelect.appendChild(opt);
        });
    }
    
    if(engine.request.supportedLanguages) {
        engine.request.supportedLanguages.forEach(l => {
            const opt = document.createElement('option'); opt.value = l.code; opt.innerText = l.name; lSelect.appendChild(opt);
        });
    }
}

function renderConfigs() {
    const list = document.getElementById('addedConfigsList');
    list.innerHTML = "";
    
    let hasInfiniteScroll = false;

    currentConfigs.forEach((c, i) => {
        const li = document.createElement('li');
        li.innerHTML = `<span><strong>${c.engineName}</strong>: ${c.countryName} (${c.langCode || 'Auto'})</span> <span class="remove-engine-btn">×</span>`;
        li.querySelector('.remove-engine-btn').onclick = () => { currentConfigs.splice(i, 1); renderConfigs(); };
        list.appendChild(li);

        const engineObj = availableEngines.find(e => e.engine.id === c.engineId);
        if (engineObj && engineObj.selectors && engineObj.selectors.pagination && engineObj.selectors.pagination.type === "infinite_scroll") {
            hasInfiniteScroll = true;
        }
    });

    const warningDiv = document.getElementById('infiniteScrollWarning');
    const limitTypeSelect = document.getElementById('sessLimitType');
    
    if (hasInfiniteScroll && warningDiv) {
        warningDiv.style.display = 'block';
        if (limitTypeSelect.value === 'PAGES') {
            limitTypeSelect.value = 'RESULTS';
            limitTypeSelect.dispatchEvent(new Event('change'));
        }
    } else if (warningDiv) {
        warningDiv.style.display = 'none';
    }
}

function renderEngineList(engines) {
    const container = document.getElementById('engineListContainer');
    container.innerHTML = "";
    engines.forEach(e => {
        const div = document.createElement('div');
        div.className = "engine-card";
        div.innerHTML = `<div><strong>${e.engine.name}</strong> <span style="font-size:10px; color:#666">v${e.engine.version || '1.0'}</span><br><small>${e.engine.id} | ${e.request.supportedCountries?.length || 0} Countries</small></div><button class="btn-info btn-sm">Edit / Test</button>`;
        div.onclick = () => openEngineEditor(e);
        container.appendChild(div);
    });
}

function openEngineEditor(engine) {
    currentEditingEngineId = engine.engine.id;
    document.getElementById('engineJsonEditor').value = JSON.stringify(engine, null, 2);
    
    document.getElementById('engineJsonEditor').dispatchEvent(new Event('input'));
    
    document.getElementById('engineListView').style.display = 'none';
    document.getElementById('engineEditView').style.display = 'block';
    
    document.getElementById('sandboxLiveLog').innerHTML = "Waiting to start test...";
    document.getElementById('sandboxResultsPreview').style.display = 'none';
    document.getElementById('sandboxPreviewLabel').style.display = 'none';
    
    document.getElementById('deleteEngineBtn').style.display = 'block'; 
    
    populateSandboxDropdowns(engine);
}

function populateSandboxDropdowns(engine) {
    const cSelect = document.getElementById('sandboxCountry');
    const lSelect = document.getElementById('sandboxLanguage');
    cSelect.innerHTML = ""; lSelect.innerHTML = "";
    
    if(engine.request && engine.request.supportedCountries) {
        engine.request.supportedCountries.forEach(c => {
            const opt = document.createElement('option'); opt.value = c.code; opt.innerText = c.name; cSelect.appendChild(opt);
        });
    }
    if(engine.request && engine.request.supportedLanguages) {
        engine.request.supportedLanguages.forEach(l => {
            const opt = document.createElement('option'); opt.value = l.code; opt.innerText = l.name; lSelect.appendChild(opt);
        });
    }
}

function showView(id) { document.querySelectorAll('.view').forEach(e => e.style.display = 'none'); document.getElementById(id).style.display = 'block'; }

function renderList(sessions) {
    const div = document.getElementById('sessionList');
    div.innerHTML = sessions.length ? "" : "<div style='color:#999;text-align:center;padding:10px'>No studies found.</div>";
    sessions.forEach(s => {
        const el = document.createElement('div');
        el.className = "session-card" + (s.status === "RUNNING" ? " session-running" : (s.status === "PAUSED_CAPTCHA" ? " session-paused-captcha" : (s.status === "QUEUED" ? " session-queued" : "")));
        el.innerHTML = `<div><strong>${esc(s.name)}</strong> <span style="font-size:10px; color:#666">[${esc(s.status === "PAUSED_CAPTCHA" ? "PAUSED (CAPTCHA)" : s.status)}]</span><br><small>Tasks: ${s.progress.done}/${s.progress.total}</small></div>`;
        el.onclick = () => openSession(s.id);
        div.appendChild(el);
    });
}

function openSession(id) { 
    currentSessionId = id;
    panelsFilledFor = null;
    lastStatus = null;
    document.getElementById('logContainer').innerHTML = "";
    document.getElementById('eProxyTestOut').innerHTML = "";
    
    cachedTasks = [];
    currentTaskPage = 1; 
    const taskContainer = document.getElementById('taskListContainer');
    if (taskContainer) taskContainer.innerHTML = "<div style='padding:10px;text-align:center'>Loading...</div>";
    const countDisplay = document.getElementById('taskCountDisplay');
    if (countDisplay) countDisplay.innerText = "0";

    showView('statusView'); 
    
    chrome.runtime.sendMessage({ action: "GET_SESSION_STATUS", payload: { sessionId: id } }); 
    
    chrome.runtime.sendMessage({ action: "GET_TASKS", payload: { sessionId: id } });
}

function updateStatus(data) {
    if (data.sessionId !== currentSessionId) return;
    lastStatus = data;
    document.getElementById('statusTitle').innerText = data.name + (data.runNumber > 1 ? ` (run ${data.runNumber})` : "");
    const statusEl = document.getElementById('statusState');
    statusEl.innerText = data.status;

    if (data.status === "PAUSED_CAPTCHA") { statusEl.style.color = "#dc3545"; statusEl.innerText = "PAUSED (CAPTCHA)"; }
    else if (data.status === "QUEUED") { statusEl.style.color = "#856404"; statusEl.innerText = "QUEUED (waiting for the running study)"; }
    else { statusEl.style.color = "black"; }

    document.getElementById('currentQuery').innerText = data.currentQuery || "-";
    document.getElementById('progressBar').style.width = (data.progress.total ? data.progress.done / data.progress.total * 100 : 0) + "%";
    document.getElementById('progressText').innerText = `${data.progress.done}/${data.progress.total} Tasks`;
    renderMetrics(data.metrics);
    renderRetryInfo();
    renderProxyOverview(data.proxy);

    if (data.logs && document.getElementById('logContainer').innerHTML === "") data.logs.forEach(addSingleLog);

    const btn = document.getElementById('playPauseBtn');
    if (data.status === "RUNNING" || data.status === "QUEUED") { btn.innerText = "Pause"; btn.classList.remove("btn-success"); btn.classList.add("btn-primary"); }
    else { btn.innerText = "Resume / Start"; btn.classList.add("btn-success"); btn.classList.remove("btn-primary"); }

    if (data.originalConfigs) {
        const list = document.getElementById('activeEnginesList');
        list.innerHTML = "";
        data.originalConfigs.forEach((conf, index) => {
            const li = document.createElement('li');
            li.innerHTML = `<span><strong>${conf.engineName}</strong>: ${conf.countryName} (${conf.langCode || 'Auto'})</span>
                            <span class="remove-engine-btn" title="Remove engine & cancel pending tasks">×</span>`;
            li.querySelector('.remove-engine-btn').onclick = (e) => {
                e.stopPropagation(); 
                if(confirm(`Remove ${conf.countryName}?\n\nThis will CANCEL all pending tasks for this engine.\nExisting results remain safe.`)) {
                    chrome.runtime.sendMessage({ action: "REMOVE_CONFIG", payload: { sessionId: currentSessionId, configIndex: index } });
                }
            };
            list.appendChild(li);
        });
    }
    
    if (data.originalQueries) document.getElementById('totalQueriesCount').innerText = data.originalQueries.length;

    if (data.settings && panelsFilledFor !== data.sessionId) {
         panelsFilledFor = data.sessionId;
         fillProxyOpts('e', data.settings);
         fillBehaviorOpts('e', data.settings);
         document.getElementById('editUseProxies').checked = data.settings.useProxies;
         document.getElementById('editProxyList').value = data.settings.proxyList ? data.settings.proxyList.join('\n') : "";
    }

    const proxyArea = document.getElementById('editProxyList');
    if (document.activeElement !== proxyArea && data.settings) {
         document.getElementById('editSaveSerp').checked = data.settings.saveSerp || data.settings.saveScreenshots || false;
         
         if (data.settings.serpLimit) {
             document.getElementById('editSessSerpLimit').value = data.settings.serpLimit;
         }
         document.getElementById('editSerpLimitContainer').style.display = document.getElementById('editSaveSerp').checked ? 'block' : 'none';
         
         setSettingBadge('badgeProxies', data.settings.useProxies);
    }

    const minInput = document.getElementById('liveMin');
    const maxInput = document.getElementById('liveMax');
    if (data.delays && document.activeElement !== minInput && document.activeElement !== maxInput) {
        minInput.value = data.delays.min / 1000;
        maxInput.value = data.delays.max / 1000;
    }

    const limitInput = document.getElementById('liveLimit');
    const limitTypeInput = document.getElementById('liveLimitType');
    if (data.globalCount && document.activeElement !== limitInput) limitInput.value = data.globalCount;
    if (data.limitType && document.activeElement !== limitTypeInput) limitTypeInput.value = data.limitType;
}

function renderMetrics(m) {
    const box = document.getElementById('metricsBox');
    if (!m) { box.innerHTML = ""; return; }
    let html = `📈 Pages: <b>${m.pages}</b> · Items: <b>${m.results}</b> · Empty pages: <b>${m.zeroPages}</b> · Captchas: <b>${m.captchas}</b> · IP rotations: <b>${m.rotations}</b>`;
    const keys = Object.keys(m.byVariant || {});
    if (keys.length > 1) {
        html += `<table class="proxy-table" style="margin-top:4px"><tr><th>Engine | country | lang</th><th>Pages</th><th>Items</th><th>Empty</th><th>Captchas</th></tr>` +
            keys.map(k => { const v = m.byVariant[k]; return `<tr><td>${esc(k.replace(/\|/g, ' | '))}</td><td>${v.pages}</td><td>${v.results}</td><td>${v.zeroPages}</td><td>${v.captchas}</td></tr>`; }).join("") + `</table>`;
    }
    box.innerHTML = html;
}

function formatCountdown(ts) {
    const s = Math.max(0, Math.round((ts - Date.now()) / 1000));
    if (s >= 3600) return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} min`;
    if (s >= 60) return `${Math.floor(s / 60)} min ${s % 60} s`;
    return `${s} s`;
}

function renderRetryInfo() {
    const el = document.getElementById('retryInfo');
    const d = lastStatus;
    if (!d || d.sessionId !== currentSessionId) { el.style.display = 'none'; return; }
    let txt = "";
    if (d.status === "PAUSED_CAPTCHA" && d.retryAt) txt = `⏳ All IPs are cooling down. Automatic retry in ${formatCountdown(d.retryAt)} (or press Resume to retry now).`;
    else if (d.status === "PAUSED_CAPTCHA") txt = `🧩 A captcha needs attention: solve it in the opened tab, then press Resume.`;
    else if (d.status === "DONE" && d.nextRunAt) txt = `🔁 Next repeat run starts in ${formatCountdown(d.nextRunAt)}.`;
    el.style.display = txt ? 'block' : 'none';
    el.innerText = txt;
}
setInterval(renderRetryInfo, 1000);

function renderProxyOverview(ov) {
    const box = document.getElementById('proxyOverviewBox');
    if (!ov || !ov.entries || !ov.entries.length) { box.style.display = 'none'; box.innerHTML = ""; return; }
    const rows = ov.entries.map((e, i) => {
        const chk = e.check ? (e.check.ok ? `<span class="ok-text">✔ ${esc(e.check.ip)}</span>` : `<span class="bad-text">✘ ${esc(e.check.error)}</span>`) : "";
        return `<tr><td>${i === ov.current ? "▶" : ""}</td><td>${esc(e.target)}</td><td>${e.requests}</td><td>${e.captchas}</td><td>${e.fails}</td><td>${e.coolingMinutes ? e.coolingMinutes + " min" : "-"}</td><td>${chk}</td></tr>`;
    }).join("");
    box.style.display = 'block';
    box.innerHTML = `<table class="proxy-table"><tr><th></th><th>Proxy</th><th>Req.</th><th>Captcha</th><th>Fails</th><th>Cooling</th><th>Test</th></tr>${rows}</table>`;
}

function setSettingBadge(id, isActive) {
    const el = document.getElementById(id);
    if(isActive) el.classList.add('setting-active');
    else el.classList.remove('setting-active');
}

function addSingleLog(entry) {
    const div = document.getElementById('logContainer');
    let color = "#333";
    if (entry.level === "WARN") color = "#856404";
    if (entry.level === "ERROR") color = "#721c24";
    div.innerHTML += `<div style="border-bottom:1px solid #eee;padding:2px 0; color:${color}">
        <span style="color:#999;margin-right:5px;font-size:10px">[${new Date(entry.ts).toLocaleTimeString()}]</span>${esc(entry.msg)}
    </div>`;
    div.scrollTop = div.scrollHeight;
}

function addConfig(c) { currentConfigs.push(c); renderConfigs(); }

function resetCreateForm() { 
    document.getElementById('sessName').value = ""; 
    document.getElementById('sessQueries').value = ""; 
    document.getElementById('saveSerp').checked = false;
    document.getElementById('serpLimitContainer').style.display = 'none'; 
    document.getElementById('sessSerpLimit').value = "100";              
    document.getElementById('useProxies').checked = false;
    document.getElementById('proxyList').value = "";
    document.getElementById('proxyList').disabled = true;
    document.getElementById('createProxyMount').style.display = 'none';
    document.getElementById('cProxyTestOut').innerHTML = "";
    document.getElementById('createErrorMsg').style.display = 'none';
    resetPanelDefaults('c');
    document.getElementById('engineFormContainer').style.display = 'none';
    document.getElementById('showEngineFormBtn').style.display = 'block';
    currentConfigs = []; 
    renderConfigs(); 
}

function renderTasks() {
    const container = document.getElementById('taskListContainer');
    const countDisplay = document.getElementById('taskCountDisplay');
    
    let filtered = cachedTasks;
    if (currentTaskFilter !== "ALL") {
        filtered = cachedTasks.filter(t => t.status === currentTaskFilter);
    }

    countDisplay.innerText = filtered.length;

    if (filtered.length === 0) {
        container.innerHTML = "<div style='padding:10px; text-align:center; color:#999; font-size:11px'>No tasks found for this filter.</div>";
        return;
    }

    const totalPages = Math.ceil(filtered.length / TASKS_PER_PAGE);
    
    if (currentTaskPage > totalPages) currentTaskPage = totalPages;
    if (currentTaskPage < 1) currentTaskPage = 1;

    const startIndex = (currentTaskPage - 1) * TASKS_PER_PAGE;
    const endIndex = startIndex + TASKS_PER_PAGE;
    const paginatedTasks = filtered.slice(startIndex, endIndex);

    let html = "";
    paginatedTasks.forEach(t => {
        const statusClass = `st-${t.status}`;
        const showDelete = (t.status === "OPEN" || t.status === "FAILED") ? "visible" : "hidden";
        const showRetry = (t.status === "FAILED") ? "inline-block" : "none";
        
        html += `
        <div class="task-item">
            <div style="flex:1; overflow:hidden;">
                <div style="font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${esc(t.term)}">${esc(t.term)}</div>
                <div style="color:#888; font-size:10px;"><strong>${esc(t.engine)}</strong> | ${esc(t.country)}</div>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="btn-secondary btn-sm" 
                    style="display:${showRetry}; padding:1px 4px; cursor:pointer;" 
                    data-action="retry" data-index="${t.index}" 
                    title="Reset this specific task">↻</span>
                
                <span class="status-badge ${statusClass}">${t.status}</span>
                
                <span class="del-task-btn" 
                    style="visibility:${showDelete}" 
                    data-action="delete" data-index="${t.index}">&times;</span>
            </div>
        </div>`;
    });

    if (totalPages > 1) {
        html += `
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px; background: #f8f9fa; border-top: 1px solid #eee;">
            <button class="btn-secondary btn-sm" data-action="prev" ${currentTaskPage === 1 ? 'disabled' : ''}>◀ Prev</button>
            <span style="font-size:11px; color:#555;">Page ${currentTaskPage} of ${totalPages}</span>
            <button class="btn-secondary btn-sm" data-action="next" ${currentTaskPage === totalPages ? 'disabled' : ''}>Next ▶</button>
        </div>`;
    }
    container.innerHTML = html;
}

function changeTaskPage(direction) {
    currentTaskPage += direction;
    renderTasks();
}

function deleteTask(index) {
    if (!currentSessionId) return;
    chrome.runtime.sendMessage({ action: "REMOVE_TASK", payload: { sessionId: currentSessionId, taskIndex: index } });
    const task = cachedTasks.find(t => t.index === index);
    if (task) { 
        task.status = "CANCELLED";
        renderTasks();
    }
}

function retryTask(index) {
    if (!currentSessionId) return;
    chrome.runtime.sendMessage({ 
        action: "RESET_TASK", 
        payload: { sessionId: currentSessionId, taskIndex: index } 
    });
    const task = cachedTasks.find(t => t.index === index);
    if (task) { 
        task.status = "OPEN"; 
        task.retryCount = 0; 
        renderTasks(); 
    }
}

function setupDragAndDropForKeywords(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;

    textarea.addEventListener('dragover', (e) => {
        e.preventDefault();
        textarea.style.border = '2px dashed #007bff';
        textarea.style.backgroundColor = '#e9ecef';
    });

    textarea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        textarea.style.border = '1px solid #ced4da';
        textarea.style.backgroundColor = '';
    });

    textarea.addEventListener('drop', (e) => {
        e.preventDefault();
        textarea.style.border = '1px solid #ced4da';
        textarea.style.backgroundColor = '';

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            
            if (file.type.includes("csv") || file.type.includes("text") || file.name.endsWith(".csv") || file.name.endsWith(".txt")) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const text = event.target.result;
                    const keywords = text.split(/[\r\n,;]+/).map(k => k.trim()).filter(k => k.length > 0);
                    const existingText = textarea.value.trim();
                    const newText = keywords.join('\n');
                    textarea.value = existingText ? existingText + '\n' + newText : newText;
                };
                reader.readAsText(file);
            } else {
                alert("Please drag a valid CSV or TXT file into the field.");
            }
        }
    });
}

document.getElementById('importDesignBtn').addEventListener('click', () => {
    document.getElementById('importDesignInput').click();
});