/**
 * @file sidepanel.js - Version 2.3 (With JSON Import/Export features)
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

// Hält alle installierten Scraper-Engines im Arbeitsspeicher des UIs
let availableEngines = []; 
let currentEditingEngineId = null;

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
    try {
        alert("Importing Backup... Please wait. Do not close this panel!");
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
    }
}

async function performFullBackup() {
    if (!dbLocal) await initLocalDB();
    alert("Generating Full Backup... This may take a while. Do not close this panel!");
    
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
        });
    } catch(e) {
        alert("Backup Error: " + e.message);
    }
}

async function performExportDataAsZip(sessionId) {
    if (!dbLocal) await initLocalDB();
    alert("Generation of export started. Please wait. Do not close this panel!");

    try {
        const session = await localGetSession(sessionId);
        const logs = await localGetLogs(sessionId);
        const zip = new JSZip();
        const imgFolder = zip.folder("screenshots");
        const htmlFolder = zip.folder("html");

        if (logs) {
            zip.file("activity_log.txt", logs.map(l => `[${l.ts}] [${l.level || 'INFO'}] ${l.msg}`).join("\n"));
        }

        let csv = "\uFEFFquery,engine,country,lang,page,type,rank,title,url,snippet,ai_full_text\n";
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
                    csv += `${meta},${p.pageNumber},ai_overview,1,AI Overview,,,${esc(p.results.ai_overview.text_full)}\n`;
                    p.results.ai_overview.sources.forEach((src, idx) => {
                        csv += `${meta},${p.pageNumber},ai_source,${idx + 1},${esc(src.title)},${esc(src.url)},,\n`;
                    });
                }

                p.results.organic.forEach(r => {
                    csv += `${meta},${p.pageNumber},organic,${r.rank},${esc(r.title)},${esc(r.url)},${esc(r.snippet)},\n`;
                });

                p.results.ads.forEach(ad => {
                    csv += `${meta},${p.pageNumber},ad,${ad.rank},${esc(ad.title)},${esc(ad.url)},${esc(ad.snippet)},\n`;
                });
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
        });

    } catch (err) {
        alert("Critical Error during Export: " + err.message);
    }
}


// --- 3. INITIALIZATION & EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    initLocalDB(); 
    
    setupDragAndDropForKeywords('sessQueries');
    setupDragAndDropForKeywords('addQueryInput');

    // Navigation Bindings
    document.getElementById('createSessionBtn').addEventListener('click', () => { resetCreateForm(); showView('createView'); });
    document.getElementById('backBtn').addEventListener('click', () => showView('listView'));
    document.getElementById('backToListBtn').addEventListener('click', () => { 
        currentSessionId = null; 
        showView('listView'); 
        chrome.runtime.sendMessage({ action: "GET_SESSIONS" }); 
    });
    
    document.getElementById('manageEnginesBtn').addEventListener('click', () => { showView('engineView'); document.getElementById('engineEditView').style.display = 'none'; document.getElementById('engineListView').style.display = 'block'; });
    document.getElementById('backToMainFromEnginesBtn').addEventListener('click', () => showView('listView'));

    // Dynamic Engine Selection Handlers
    document.getElementById('confEngineSelect').addEventListener('change', (e) => populateDropdowns(e.target.value, 'confCountrySelect', 'confLangSelect'));
    document.getElementById('editConfEngineSelect').addEventListener('change', (e) => populateDropdowns(e.target.value, 'editConfCountrySelect', 'editConfLangSelect'));

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

    // Add Task Config to Session Build
    document.getElementById('addConfigBtn').addEventListener('click', () => {
        const engineId = document.getElementById('confEngineSelect').value;
        const countryCode = document.getElementById('confCountrySelect').value;
        const langCode = document.getElementById('confLangSelect').value;
        const location = document.getElementById('confLoc').value.trim();
        
        const engine = availableEngines.find(e => e.engine.id === engineId);
        if (engine && countryCode) {
            const countryData = engine.request.supportedCountries.find(c => c.code === countryCode);
            addConfig({
                engineId: engine.engine.id,
                engineName: engine.engine.name,
                countryName: countryData.name,
                countryCode: countryData.code,
                domain: countryData.domain || "",
                langCode: langCode || "", 
                location: location
            });
            document.getElementById('engineFormContainer').style.display = 'none';
            document.getElementById('showEngineFormBtn').style.display = 'block';
            document.getElementById('confLoc').value = ""; 
        } else { alert("Please select a Country."); }
    });

    document.getElementById('useProxies').addEventListener('change', (e) => {
        document.getElementById('proxyList').disabled = !e.target.checked;
    });

    // Create Session Submission
    document.getElementById('startScrapeBtn').addEventListener('click', () => {
        const name = document.getElementById('sessName').value.trim();
        const q = document.getElementById('sessQueries').value.split('\n').filter(x => x.trim());
        const useProxies = document.getElementById('useProxies').checked;
        const proxyListStr = document.getElementById('proxyList').value;
        const saveSerp = document.getElementById('saveSerp').checked;
        const errorDiv = document.getElementById('createErrorMsg');
        
        errorDiv.style.display = 'none'; 
        if (!name) { errorDiv.innerText = "⚠️ Please enter a Session Name."; errorDiv.style.display = 'block'; return; }
        if (q.length === 0) { errorDiv.innerText = "⚠️ Please enter at least one Search Query."; errorDiv.style.display = 'block'; return; }
        if (currentConfigs.length === 0) { errorDiv.innerText = "⚠️ Please add at least one Search Engine configuration."; errorDiv.style.display = 'block'; return; }

        if (name && q.length > 0 && currentConfigs.length > 0) {
            chrome.runtime.sendMessage({
                action: "CREATE_SESSION",
                payload: { 
                    name, queries: q, configs: currentConfigs, 
                    resultsLimit: parseInt(document.getElementById('sessLimit').value), 
                    delays: { 
                        min: parseInt(document.getElementById('sessMin').value) * 1000, 
                        max: parseInt(document.getElementById('sessMax').value) * 1000 
                    },
                    saveSerp, useProxies, proxyListStr
                }
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
        if(currentSessionId && limit) {
            chrome.runtime.sendMessage({ action: "UPDATE_LIMIT", payload: { sessionId: currentSessionId, limit: limit }});
            alert(`Target Result Quota updated to ${limit}.`);
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
            
            const newConfig = {
                engineId: engine.engine.id,
                engineName: engine.engine.name, 
                countryName: countryData.name,
                countryCode: countryData.code, 
                domain: countryData.domain || "",
                langCode: langCode || "", 
                location: location
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
            chrome.runtime.sendMessage({ action: "UPDATE_PROXIES", payload: { sessionId: currentSessionId, useProxies, proxyListStr } });
            alert("Proxy settings updated.");
        }
    });

    document.getElementById('saveStorageSettingsBtn').addEventListener('click', () => {
        const saveSerp = document.getElementById('editSaveSerp').checked;
        if(currentSessionId) {
            chrome.runtime.sendMessage({ action: "UPDATE_STORAGE_SETTINGS", payload: { sessionId: currentSessionId, saveSerp } });
            alert("Storage settings updated.");
        }
    });

    document.getElementById('refreshTasksBtn').addEventListener('click', () => {
        if(currentSessionId) {
            document.getElementById('taskListContainer').innerHTML = "<div style='padding:10px;text-align:center'>Loading...</div>";
            chrome.runtime.sendMessage({ action: "GET_TASKS", payload: { sessionId: currentSessionId } });
        }
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
            renderTasks();
        });
    });

    // --- NEU: ENGINE MANAGER (VISUAL BUILDER, SANDBOX, IMPORT & EXPORT) ---

    // TWO-WAY BINDING: JSON -> Visual Builder
    function updateVisualBuilderFromJson() {
        try {
            const j = JSON.parse(document.getElementById('engineJsonEditor').value);
            document.getElementById('vbEngineName').value = j.engine?.name || "";
            document.getElementById('vbEngineId').value = j.engine?.id || "";
            document.getElementById('vbBaseUrl').value = j.request?.baseUrl || "";
            document.getElementById('vbParamQuery').value = j.request?.params?.query || "";
            
            document.getElementById('vbSelContainer').value = j.selectors?.organic?.container || "";
            document.getElementById('vbSelTitle').value = j.selectors?.organic?.title || "";
            document.getElementById('vbSelUrl').value = j.selectors?.organic?.url || "";
            
            let snippetSel = j.selectors?.organic?.snippet;
            document.getElementById('vbSelSnippet').value = (typeof snippetSel === 'object') ? (snippetSel?.selector || "") : (snippetSel || "");
            
            document.getElementById('vbSelNext').value = j.selectors?.pagination?.nextButton || "";

            // NEU: Ads
            document.getElementById('vbSelAdContainer').value = j.selectors?.ads?.container || "";
            document.getElementById('vbSelAdTitle').value = j.selectors?.ads?.title || "";
            document.getElementById('vbSelAdUrl').value = j.selectors?.ads?.url || "";
            let adSnippetSel = j.selectors?.ads?.snippet;
            document.getElementById('vbSelAdSnippet').value = (typeof adSnippetSel === 'object') ? (adSnippetSel?.selector || "") : (adSnippetSel || "");

            // NEU: AI Overview
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
            
            // Organic
            j.selectors.organic = j.selectors.organic || {};
            j.selectors.organic.container = document.getElementById('vbSelContainer').value;
            j.selectors.organic.title = document.getElementById('vbSelTitle').value;
            j.selectors.organic.url = document.getElementById('vbSelUrl').value;
            let snippetVal = document.getElementById('vbSelSnippet').value;
            if (typeof j.selectors.organic.snippet === 'object') {
                j.selectors.organic.snippet.selector = snippetVal;
            } else { j.selectors.organic.snippet = snippetVal; }
            
            j.selectors.pagination = j.selectors.pagination || {};
            j.selectors.pagination.nextButton = document.getElementById('vbSelNext').value;

            // NEU: Ads
            j.selectors.ads = j.selectors.ads || {};
            j.selectors.ads.container = document.getElementById('vbSelAdContainer').value || null;
            j.selectors.ads.title = document.getElementById('vbSelAdTitle').value || null;
            j.selectors.ads.url = document.getElementById('vbSelAdUrl').value || null;
            let adSnippetVal = document.getElementById('vbSelAdSnippet').value;
            if (typeof j.selectors.ads.snippet === 'object') {
                j.selectors.ads.snippet.selector = adSnippetVal || null;
            } else { j.selectors.ads.snippet = adSnippetVal || null; }

            // NEU: AI Overview
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

    // Event Listener für die Visual Builder Inputs (mit allen neuen IDs)
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

    // Event Listener für den JSON Editor
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
        document.getElementById('engineJsonEditor').value = `{\n  "manifest_version": 1,\n  "engine": {\n    "id": "new_scraper",\n    "name": "My Custom Engine"\n  },\n  "request": {\n    "baseUrl": "https://{domain}/search",\n    "params": {\n      "query": "q",\n      "country": "gl",\n      "language": "hl"\n    },\n    "features": { "requiresUuleEncoding": false, "urlDecodingMethod": "none" },\n    "supportedCountries": [\n      { "code": "us", "name": "USA", "domain": "www.example.com" }\n    ],\n    "supportedLanguages": [\n      { "code": "en", "name": "English" }\n    ]\n  },\n  "behavior": {},\n  "captcha": {},\n  "selectors": {\n    "pagination": { "nextButton": ".next" },\n    "organic": {\n      "container": ".result",\n      "title": "h2",\n      "url": "a",\n      "snippet": { "selector": ".snippet" }\n    },\n    "ads": { "container": ".ad", "title": "h2", "url": "a", "snippet": { "selector": ".snippet" } },\n    "ai_overview": { "container": null, "text": null, "sources": null }\n  }\n}`;
        updateVisualBuilderFromJson();
        
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
        
        const confirmMsg = "Are you sure you want to delete this scraper permanently?\n\nMöchtest du diesen Scraper wirklich dauerhaft löschen? Diese Aktion kann nicht rückgängig gemacht werden.";
        
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

    // Helper für Sandbox UI
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

    // THE MAGIC SANDBOX EXECUTION
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

            // --- PAGINATION LOOP FÜR DIE SANDBOX ---
            let collectedOrganic = [];
            let collectedAds = [];
            let aiOverviewData = null;
            let currentPage = 1;
            const targetResults = 20; // Sandbox sucht nun solange, bis 20 Ergebnisse erreicht sind
            const existingUrls = new Set();
            
            while (collectedOrganic.length < targetResults && currentPage <= 5) {
                // NEU: Wir injizieren das Skript bei JEDER Seite neu!
                // Das ist überlebenswichtig für Google, weil Google bei "Next" die Seite neu lädt.
                await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] }).catch(() => {});
                
                logToSandbox(`📜 Page ${currentPage}: Executing human logic & scrolling...`);
                await chrome.tabs.sendMessage(tab.id, { action: "SCROLL_AND_PREPARE", payload: { config: engineConfig } }).catch(()=>{});
                
                // Wichtig: Extra Wartezeit, damit AI Overviews nachladen können
                await new Promise(r => setTimeout(r, 2500));
                
                logToSandbox(`🔍 Page ${currentPage}: Extracting Data using JSON selectors...`);
                const response = await chrome.tabs.sendMessage(tab.id, { action: "SCRAPE_SERP", payload: { startRank: collectedOrganic.length, config: engineConfig } }).catch(() => null);

                if (response && response.data) {
                    const data = response.data;
                    
                    const newOrganic = data.organic.filter(r => !existingUrls.has(r.url));
                    newOrganic.forEach(r => existingUrls.add(r.url));
                    
                    collectedOrganic = collectedOrganic.concat(newOrganic);
                    collectedAds = collectedAds.concat(data.ads);
                    
                    // --- NEUE, DETAILLIERTE LOGS FÜR AI & ADS ---
                    if (data.ai_overview && data.ai_overview.found) {
                        if (!aiOverviewData) aiOverviewData = data.ai_overview; // Für die finale Vorschau speichern
                        const sourceCount = data.ai_overview.sources ? data.ai_overview.sources.length : 0;
                        logToSandbox(`🤖 AI Overview / Search Assist successfully extracted! (${sourceCount} sources found)`, "#17a2b8");
                    }

                    if (data.ads && data.ads.length > 0) {
                        logToSandbox(`📢 Extracted ${data.ads.length} Ad(s) on Page ${currentPage}.`, "#fd7e14");
                    }

                    // Einheitliche Zusammenfassung
                    const aiFoundStr = (data.ai_overview && data.ai_overview.found) ? "Yes" : "No";
                    logToSandbox(`📊 Page ${currentPage} Summary: AI: ${aiFoundStr} | Ads: ${data.ads.length} | New Organic: ${newOrganic.length} (Total: ${collectedOrganic.length}/${targetResults})`);
                    // ---------------------------------------------

                    // Preview des ersten Snippets NUR im Sandbox Log anzeigen
                    if (newOrganic.length > 0) {
                        const firstRes = newOrganic[0];
                        const shortSnippet = firstRes.snippet ? firstRes.snippet.substring(0, 60).replace(/\n/g, ' ') + "..." : "No snippet found";
                        logToSandbox(`📝 Preview Rank ${collectedOrganic.length - newOrganic.length + 1}: "${firstRes.title.substring(0,30)}..." - ${shortSnippet}`, "#555");
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
                        // Längere Wartezeit hier, damit Google den Hard-Reload sauber durchführen kann
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

            // --- ERGEBNISSE ANZEIGEN ---
            const previewDiv = document.getElementById('sandboxResultsPreview');
            let html = "";
            
            if (aiOverviewData) {
                html += `<div class="sandbox-card" style="border-color:#17a2b8; background:#e0f7fa;">
                    <div class="sandbox-card-title">🤖 AI Overview Detected</div>
                    <div class="sandbox-card-snippet">${aiOverviewData.text_full.substring(0, 150)}...</div>
                    <div style="font-size:10px; color:#666; margin-top:5px;">Sources: ${aiOverviewData.sources.length} extracted</div>
                </div>`;
            }

            collectedOrganic.slice(0, targetResults).forEach((res, idx) => {
                html += `<div class="sandbox-card">
                    <div style="font-size:10px; color:#888;">Rank ${idx + 1}</div>
                    <div class="sandbox-card-title">${res.title}</div>
                    <div class="sandbox-card-url">${res.url}</div>
                    <div class="sandbox-card-snippet">${res.snippet}</div>
                </div>`;
            });

            previewDiv.innerHTML = html;
            previewDiv.style.display = 'block';
            document.getElementById('sandboxPreviewLabel').style.display = 'block';
            
            // Tab schließen nach dem Test
            chrome.tabs.remove(tab.id).catch(()=>{});

        } catch(err) {
            logToSandbox(`❌ CRITICAL ERROR: ${err.message}`, "#721c24");
        }
    });

    // Start-Up Calls
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
        el.className = "session-card" + (s.status === "RUNNING" ? " session-running" : (s.status === "PAUSED_CAPTCHA" ? " session-paused-captcha" : ""));
        el.innerHTML = `<strong>${s.name}</strong> <span style="font-size:10px; color:#666">[${s.status}]</span><br><small>Tasks: ${s.progress.done}/${s.progress.total}</small>`;
        el.onclick = () => openSession(s.id);
        div.appendChild(el);
    });
}

function openSession(id) { 
    currentSessionId = id; 
    document.getElementById('logContainer').innerHTML = ""; 
    showView('statusView'); 
    chrome.runtime.sendMessage({ action: "GET_SESSION_STATUS", payload: { sessionId: id } }); 
}

function updateStatus(data) {
    if (data.sessionId !== currentSessionId) return;
    document.getElementById('statusTitle').innerText = data.name;
    const statusEl = document.getElementById('statusState');
    statusEl.innerText = data.status;
    
    if (data.status === "PAUSED_CAPTCHA") { statusEl.style.color = "#dc3545"; statusEl.innerText = "PAUSED (CAPTCHA)"; } 
    else { statusEl.style.color = "black"; }

    document.getElementById('currentQuery').innerText = data.currentQuery || "-";
    document.getElementById('progressBar').style.width = (data.progress.done / data.progress.total * 100) + "%";
    document.getElementById('progressText').innerText = `${data.progress.done}/${data.progress.total} Tasks`;
    
    if (data.logs && document.getElementById('logContainer').innerHTML === "") data.logs.forEach(addSingleLog);
    
    const btn = document.getElementById('playPauseBtn');
    if (data.status === "RUNNING") { btn.innerText = "Pause"; btn.classList.remove("btn-success"); btn.classList.add("btn-primary"); } 
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

    const proxyArea = document.getElementById('editProxyList');
    if (document.activeElement !== proxyArea && data.settings) {
         document.getElementById('editUseProxies').checked = data.settings.useProxies;
         document.getElementById('editProxyList').value = data.settings.proxyList ? data.settings.proxyList.join('\n') : "";
         
         document.getElementById('editSaveSerp').checked = data.settings.saveSerp || data.settings.saveScreenshots || false;
         
         setSettingBadge('badgeProxies', data.settings.useProxies);
    }

    const minInput = document.getElementById('liveMin');
    const maxInput = document.getElementById('liveMax');
    if (data.delays && document.activeElement !== minInput && document.activeElement !== maxInput) {
        minInput.value = data.delays.min / 1000;
        maxInput.value = data.delays.max / 1000;
    }

    const limitInput = document.getElementById('liveLimit');
    if (data.globalCount && document.activeElement !== limitInput) limitInput.value = data.globalCount;
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
        <span style="color:#999;margin-right:5px;font-size:10px">[${new Date(entry.ts).toLocaleTimeString()}]</span>${entry.msg}
    </div>`;
    div.scrollTop = div.scrollHeight;
}

function addConfig(c) { currentConfigs.push(c); renderConfigs(); }

function renderConfigs() {
    const list = document.getElementById('addedConfigsList');
    list.innerHTML = "";
    currentConfigs.forEach((c, i) => {
        const li = document.createElement('li');
        li.innerHTML = `<span><strong>${c.engineName}</strong>: ${c.countryName} (${c.langCode || 'Auto'})</span> <span class="remove-engine-btn">×</span>`;
        li.querySelector('.remove-engine-btn').onclick = () => { currentConfigs.splice(i, 1); renderConfigs(); };
        list.appendChild(li);
    });
}

function resetCreateForm() { 
    document.getElementById('sessName').value = ""; 
    document.getElementById('sessQueries').value = ""; 
    document.getElementById('saveSerp').checked = false;
    document.getElementById('useProxies').checked = false;
    document.getElementById('proxyList').value = "";
    document.getElementById('proxyList').disabled = true;
    document.getElementById('engineFormContainer').style.display = 'none';
    document.getElementById('showEngineFormBtn').style.display = 'block';
    currentConfigs = []; 
    renderConfigs(); 
}

function renderTasks() {
    const container = document.getElementById('taskListContainer');
    const countDisplay = document.getElementById('taskCountDisplay');
    
    let filtered = cachedTasks;
    if (currentTaskFilter !== "ALL") filtered = cachedTasks.filter(t => t.status === currentTaskFilter);

    countDisplay.innerText = filtered.length;

    if (filtered.length === 0) {
        container.innerHTML = "<div style='padding:10px; text-align:center; color:#999; font-size:11px'>No tasks found for this filter.</div>";
        return;
    }

    let html = "";
    filtered.forEach(t => {
        const statusClass = `st-${t.status}`;
        const showDelete = (t.status === "OPEN" || t.status === "FAILED") ? "visible" : "hidden";
        
        const safeCountry = (t.country || 'US').toUpperCase();
        
        html += `
        <div class="task-item">
            <div style="flex:1; overflow:hidden;">
                <div style="font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${t.term}">${t.term}</div>
                <div style="color:#888; font-size:10px;"><strong>${t.engine}</strong> | ${safeCountry} - ${t.lang || 'Auto'}</div>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="status-badge ${statusClass}">${t.status}</span>
                <span class="del-task-btn" style="visibility:${showDelete}" onclick="deleteTask(${t.index})">&times;</span>
            </div>
        </div>`;
    });

    container.innerHTML = html;
}

window.deleteTask = function(index) {
    if(!currentSessionId) return;
    chrome.runtime.sendMessage({ action: "REMOVE_TASK", payload: { sessionId: currentSessionId, taskIndex: index } });
    const task = cachedTasks.find(t => t.index === index);
    if(task) { task.status = "CANCELLED"; renderTasks(); }
};

// --- DRAG & DROP FÜR KEYWORDS ---
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