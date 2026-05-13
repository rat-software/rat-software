/**
 * @file background.js - Version 2.0 (Plugin Engine Ready)
 * Core Service Worker for the Result Assessment Tool (RAT).
 * Handles persistence (IndexedDB), proxy rotation, and the main scraping queue.
 * Now dynamically loads JSON scrapers (Engines) instead of hardcoding logic.
 */

// --- 1. POWER ---
try {
    chrome.power.requestKeepAwake('system');
} catch (e) {
    console.warn("Power API not available (Add 'power' to manifest).");
}

// --- 1. CONFIGURATION & STATE ---
const DB_NAME = "RAT_Database";
const STORE_SESSIONS = "sessions"; 
const STORE_RESULTS = "results";   
const STORE_LOGS = "logs";         
const STORE_ENGINES = "engines";
const MAX_PAGES = 100;              

const RETRY_DELAYS = [5, 15, 30, 60]; 
let activeCaptchaListeners = {};      
let db;                               
let currentProxyAuth = null;          

chrome.webRequest.onAuthRequired.addListener(
    (details) => {
        if (currentProxyAuth) {
            return {
                authCredentials: {
                    username: currentProxyAuth.username,
                    password: currentProxyAuth.password
                }
            };
        }
        return {}; 
    },
    { urls: ["<all_urls>"] },
    ["blocking"]
);

async function setRandomProxy(sessionId, proxyList) {
    if (!proxyList || proxyList.length === 0) return false;

    const randomLine = proxyList[Math.floor(Math.random() * proxyList.length)];
    const parts = randomLine.trim().split(':');

    if (parts.length !== 4) {
        logToSession(sessionId, "⚠️ Invalid Proxy Format (Expected IP:Port:User:Pass).", "WARN");
        return false;
    }

    const [ip, port, user, pass] = parts;

    const config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: { scheme: "http", host: ip, port: parseInt(port) },
            bypassList: ["localhost", "127.0.0.1"]
        }
    };

    currentProxyAuth = { username: user, password: pass };

    return new Promise((resolve) => {
        chrome.proxy.settings.set({ value: config, scope: 'regular' }, () => {
            logToSession(sessionId, `🛡️ Proxy switched to ${ip} (Auth injected)`);
            resolve(true);
        });
    });
}

chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name.startsWith("retry_session_")) {
        const sessionId = alarm.name.replace("retry_session_", "");
        
        const storage = await chrome.storage.local.get([`retry_${sessionId}`, `tab_${sessionId}`]);
        const tabId = storage[`tab_${sessionId}`];
        let currentRetries = storage[`retry_${sessionId}`] || 0;

        if (!db) await initDB();
        
        logToSession(sessionId, `⏰ ALARM: Time's up. Service worker awakened. Starting restart...`, "INFO");

        if (tabId) {
            try { await chrome.tabs.remove(tabId); } catch(e) {}
        }

        currentRetries++;
        await chrome.storage.local.set({ [`retry_${sessionId}`]: currentRetries });

        resumeSession(sessionId);
    }
});

// --- 2. INITIALIZATION (DB & ENGINES) ---
async function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 8); // Versionsnummer beibehalten

        request.onupgradeneeded = (event) => {
            db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_SESSIONS)) db.createObjectStore(STORE_SESSIONS, { keyPath: "id" });
            if (!db.objectStoreNames.contains(STORE_RESULTS)) db.createObjectStore(STORE_RESULTS);
            if (!db.objectStoreNames.contains(STORE_LOGS)) db.createObjectStore(STORE_LOGS, { autoIncrement: true });
            if (!db.objectStoreNames.contains(STORE_ENGINES)) db.createObjectStore(STORE_ENGINES, { keyPath: "engine.id" });
        };

        request.onsuccess = async (event) => {
            db = event.target.result;
            
            await syncDefaultEngines();
            
            resolve();
        };

        request.onerror = (event) => {
            console.error("Database error: " + event.target.errorCode);
            reject("DB Error");
        };
    });
}

// --- HELPER FUNCTION ---
async function syncDefaultEngines() {
    // 1. Retrieve a list of all engine IDs currently in the database
    const existingEngineIds = await new Promise((resolve) => {
        const tx = db.transaction(STORE_ENGINES, "readonly");
        const req = tx.objectStore(STORE_ENGINES).getAllKeys();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
    });

    let engineFilesToLoad = [];
    
    // 2. Load the table of contents (index.json) from the folder
    try {
        const indexUrl = chrome.runtime.getURL('engines/index.json');
        const indexResponse = await fetch(indexUrl);
        if (!indexResponse.ok) throw new Error("index.json not found");
        engineFilesToLoad = await indexResponse.json();
    } catch (err) {
        console.error("❌ Could not load engines/index.json:", err);
        return; // Abort if the index file is missing
    }

    const enginesToSave = [];

    // 3. Load all JSONs based on the index file
    for (const fileName of engineFilesToLoad) {
        try {
            const url = chrome.runtime.getURL(`engines/${fileName}`);
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const engineJson = await response.json();
            
            // Check if the engine is already in the DB
            if (!existingEngineIds.includes(engineJson.engine.id)) {
                enginesToSave.push(engineJson);
            }
        } catch (err) {
            console.error(`❌ Error loading ${fileName}:`, err);
        }
    }

    if (enginesToSave.length === 0) return; // Nothing new to add!

    // 4. Save ONLY the new engines to the database
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_ENGINES, "readwrite");
        const store = tx.objectStore(STORE_ENGINES);
        
        enginesToSave.forEach(engine => {
            store.put(engine);
            console.log(`✅ Synced new engine via index.json: ${engine.engine.name}`);
        });

        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
    });
}

// --- ENGINE HELPERS ---
async function saveEngine(engineConfig) {
    if (!db) await initDB();
    const tx = db.transaction(STORE_ENGINES, "readwrite");
    tx.objectStore(STORE_ENGINES).put(engineConfig);
    return new Promise(r => tx.oncomplete = r);
}

async function getEngine(id) {
    if (!db) await initDB();
    return new Promise(r => {
        const tx = db.transaction(STORE_ENGINES, "readonly");
        const req = tx.objectStore(STORE_ENGINES).get(id);
        req.onsuccess = () => r(req.result);
    });
}

async function getAllEngines() {
    if (!db) await initDB();
    return new Promise(r => {
        const tx = db.transaction(STORE_ENGINES, "readonly");
        const req = tx.objectStore(STORE_ENGINES).getAll();
        req.onsuccess = () => r(req.result);
    });
}

async function deleteEngine(id) {
    if (!db) await initDB();
    const tx = db.transaction(STORE_ENGINES, "readwrite");
    tx.objectStore(STORE_ENGINES).delete(id);
    return new Promise(r => tx.oncomplete = r);
}

// --- 3. LOGGING ENGINE ---
async function logToSession(sessionId, text, level = "INFO") {
    if (!db) await initDB();
    const entry = { sessionId, ts: new Date().toISOString(), msg: text, level: level };
    const tx = db.transaction(STORE_LOGS, "readwrite");
    tx.objectStore(STORE_LOGS).add(entry);
    chrome.runtime.sendMessage({ type: "LOG_ENTRY", payload: { sessionId, entry } }).catch(() => { });
}

async function getLogs(sessionId) {
    if (!db) await initDB();
    return new Promise(r => {
        const tx = db.transaction(STORE_LOGS, "readonly");
        const req = tx.objectStore(STORE_LOGS).getAll();
        req.onsuccess = () => r(req.result.filter(l => l.sessionId === sessionId));
    });
}

// --- 4. DATA HELPERS ---
async function saveSession(session) {
    if (!db) await initDB();
    const tx = db.transaction(STORE_SESSIONS, "readwrite");
    tx.objectStore(STORE_SESSIONS).put(session);
    return new Promise(r => tx.oncomplete = r);
}

async function getSession(id) {
    if (!db) await initDB();
    const tx = db.transaction(STORE_SESSIONS, "readonly");
    return new Promise(r => {
        const req = tx.objectStore(STORE_SESSIONS).get(id);
        req.onsuccess = () => r(req.result);
    });
}

async function getAllSessions() {
    if (!db) await initDB();
    const tx = db.transaction(STORE_SESSIONS, "readonly");
    return new Promise(r => {
        const req = tx.objectStore(STORE_SESSIONS).getAll();
        req.onsuccess = () => r(req.result);
    });
}

async function savePageContent(sessionId, taskIdx, pageNum, content) {
    const tx = db.transaction(STORE_RESULTS, "readwrite");
    tx.objectStore(STORE_RESULTS).put(content, `${sessionId}_${taskIdx}_${pageNum}`);
}

async function isPaused(sessionId) {
    const s = await getSession(sessionId);
    return (!s || (s.status !== "RUNNING"));
}

// --- 5. MESSAGING & ROUTING ---
chrome.runtime.onInstalled.addListener(async () => {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => { });
    await initDB();
    chrome.proxy.settings.clear({ scope: 'regular' }); 
});

chrome.runtime.onStartup.addListener(() => initDB());

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    handleMessage(msg).then(sendResponse);
    return true; 
});

async function handleMessage(msg) {
    if (!db) await initDB();
    switch (msg.action) {
        case "GET_SESSIONS": broadcastSessionList(); break;
        case "CREATE_SESSION": createNewSession(msg.payload); break;
        case "GET_SESSION_STATUS": if (msg.payload.sessionId) broadcastSessionStatus(msg.payload.sessionId); break;
        case "START": if (msg.payload.sessionId) startSession(msg.payload.sessionId); break;
        case "PAUSE": if (msg.payload.sessionId) pauseSession(msg.payload.sessionId); break;
        case "DELETE_SESSION": if (msg.payload.sessionId) deleteSession(msg.payload.sessionId); break;
        case "UPDATE_DELAY": updateSessionDelay(msg.payload); break;
        case "UPDATE_LIMIT": updateSessionLimit(msg.payload); break; 
        case "ADD_ITEMS": addItemsToSession(msg.payload); break;
        case "UPDATE_PROXIES": updateSessionProxies(msg.payload); break;
        case "REMOVE_CONFIG": removeConfigFromSession(msg.payload); break;
        case "GET_TASKS": broadcastSessionTasks(msg.payload.sessionId); break;
        case "REMOVE_TASK": removeSingleTask(msg.payload); break;
        case "UPDATE_STORAGE_SETTINGS": updateSessionStorageSettings(msg.payload); break;
        case "GET_ENGINES": broadcastEngines(); break;
        case "SAVE_ENGINE": saveEngine(msg.payload).then(() => broadcastEngines()); break;
        case "DELETE_ENGINE": deleteEngine(msg.payload.id).then(() => broadcastEngines()); break;
        case "RESET_TASK": 
            if (msg.payload.sessionId) resetSingleTask(msg.payload); 
            break;
    }
}

async function broadcastEngines() {
    const engines = await getAllEngines();
    chrome.runtime.sendMessage({ type: "ENGINE_LIST", payload: engines }).catch(() => { });
}

// --- 6. CAPTCHA HANDLING ---
async function handleCaptchaEvent(sessionId, tabId) {
    const s = await getSession(sessionId);
    if (!s || s.status !== "RUNNING") return;

    // Load the current engine config
    const currentTask = s.tasks[s.currentIndex];
    let engineConfig = null;
    if (currentTask && currentTask.config && currentTask.config.engineId) {
        engineConfig = await getEngine(currentTask.config.engineId);
    }

    s.status = "PAUSED_CAPTCHA";
    await saveSession(s);
    broadcastSessionStatus(sessionId);

    const storageKeyRetry = `retry_${sessionId}`;
    const storageKeyProxyTry = `proxy_try_${sessionId}`;
    
    const storage = await chrome.storage.local.get([storageKeyRetry, storageKeyProxyTry]);
    const retryCount = storage[storageKeyRetry] || 0;
    const proxyTryCount = storage[storageKeyProxyTry] || 0;

    const useProxies = s.settings && s.settings.useProxies;
    const proxyList = s.settings && s.settings.proxyList || [];

    if (useProxies && proxyList.length > 0 && proxyTryCount < 3) {
        logToSession(sessionId, `🛡️ CAPTCHA detected. Attempt proxy change (${proxyTryCount + 1}/3)...`, "WARN");
        cleanupCaptchaHandling(sessionId);
        await setRandomProxy(sessionId, proxyList);
        try { await chrome.tabs.remove(tabId); } catch(e) {}
        await chrome.storage.local.set({ [storageKeyProxyTry]: proxyTryCount + 1 });
        logToSession(sessionId, "🔄 Task restart with new IP...", "INFO");
        resumeSession(sessionId);
        return; 
    }

    if (proxyTryCount >= 3) {
        logToSession(sessionId, "❌ 3 proxy attempts failed. Disable proxies & switch to long-term mode.", "ERROR");
        await new Promise(r => chrome.proxy.settings.clear({ scope: 'regular' }, r));
        currentProxyAuth = null;
        logToSession(sessionId, "🌍 Connection reset to Direct Connection.", "INFO");
        try { await chrome.tabs.reload(tabId); } catch(e) {}
        await chrome.storage.local.set({ [storageKeyProxyTry]: 0 });
    }

    await chrome.storage.local.set({ [`tab_${sessionId}`]: tabId });
    const retryLevel = Math.min(retryCount, RETRY_DELAYS.length - 1);
    const waitMinutes = RETRY_DELAYS[retryLevel];
    
    logToSession(sessionId, `🛡️ Automation paused.`, "WARN");
    logToSession(sessionId, `👉 A: Manual solve (monitoring tab...).`, "INFO");
    logToSession(sessionId, `👉 B: Auto-Retry via alarm in ${waitMinutes} minutes.`, "INFO");

    cleanupCaptchaHandling(sessionId);

    const onTabUpdated = async (updatedTabId, changeInfo, tab) => {
        if (updatedTabId !== tabId) return;
        const currentUrl = (tab.url || changeInfo.url || "").toLowerCase();
        
        const seemsSafe = !currentUrl.includes("sorry") && !currentUrl.includes("captcha");

        if (seemsSafe && !onTabUpdated.isResolving) {
            onTabUpdated.isResolving = true; 
            await sleep(1500); 
            try {
                let check = await chrome.tabs.sendMessage(tabId, { action: "CHECK_CAPTCHA", payload: { config: engineConfig } }).catch(() => null);
                if (!check) {
                    await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] }).catch(() => {});
                    await sleep(500);
                    check = await chrome.tabs.sendMessage(tabId, { action: "CHECK_CAPTCHA", payload: { config: engineConfig } }).catch(() => null);
                }
                if (check && !check.isCaptcha) {
                    logToSession(sessionId, "✅ URL clean & captcha gone! Continue...", "SUCCESS");
                    cleanupCaptchaHandling(sessionId);
                    await chrome.storage.local.set({ [storageKeyRetry]: 0, [storageKeyProxyTry]: 0 });
                    resumeSession(sessionId);
                } else {
                    onTabUpdated.isResolving = false;
                }
            } catch (e) {
                onTabUpdated.isResolving = false;
            }
        }
    };

    chrome.tabs.onUpdated.addListener(onTabUpdated);
    activeCaptchaListeners[sessionId] = onTabUpdated;
    chrome.alarms.create(`retry_session_${sessionId}`, { delayInMinutes: waitMinutes });
}

function cleanupCaptchaHandling(sessionId) {
    chrome.alarms.clear(`retry_session_${sessionId}`);
    if (activeCaptchaListeners[sessionId]) {
        chrome.tabs.onUpdated.removeListener(activeCaptchaListeners[sessionId]);
        delete activeCaptchaListeners[sessionId];
    }
}

async function resumeSession(sessionId) {
    if (!db) await initDB();
    const s = await getSession(sessionId);
    if (s) {
        s.status = "RUNNING";
        await saveSession(s);
        broadcastSessionStatus(sessionId);
        processQueue(sessionId);
    }
}

// --- 7. SCRAPER CORE ---
async function broadcastSessionTasks(sessionId) {
    const session = await getSession(sessionId);
    if (!session) return;

    const simplifiedTasks = session.tasks.map((t, index) => ({
        index: index,
        term: t.term,
        engine: t.config.engineName || "Google",
        country: t.config.countryCode,
        lang: t.config.langCode,
        status: t.status,
        retryCount: t.retryCount
    }));

    chrome.runtime.sendMessage({
        type: "TASK_LIST_UPDATE",
        payload: { sessionId, tasks: simplifiedTasks }
    }).catch(() => {});
}

async function removeSingleTask(payload) {
    const { sessionId, taskIndex } = payload;
    const session = await getSession(sessionId);
    if (!session) return;

    const task = session.tasks[taskIndex];
    if (!task) return;

    if (task.status === "DONE") {
        logToSession(sessionId, "⚠️ Cannot remove completed task.", "WARN");
        return;
    }

    task.status = "CANCELLED";
    await saveSession(session);
    
    broadcastSessionStatus(sessionId); 
    broadcastSessionTasks(sessionId);  
}

async function addItemsToSession(payload) {
    const { sessionId, newQueries, newConfigs } = payload;
    const session = await getSession(sessionId);
    if (!session) return;

    let newTasks = [];

    if (newQueries && newQueries.length > 0) {
        const configsToRun = session.originalConfigs; 
        const tasks = newQueries.flatMap(q => configsToRun.map(conf => ({
            term: q, config: conf, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0
        })));
        newTasks = newTasks.concat(tasks);
        session.originalQueries = [...session.originalQueries, ...newQueries];
        logToSession(sessionId, `➕ Added ${newQueries.length} new queries.`);
    }

    if (newConfigs && newConfigs.length > 0) {
        const queriesToRun = session.originalQueries;
        const tasks = queriesToRun.flatMap(q => newConfigs.map(conf => ({
            term: q, config: conf, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0
        })));
        newTasks = newTasks.concat(tasks);
        session.originalConfigs = [...session.originalConfigs, ...newConfigs];
        logToSession(sessionId, `➕ Added ${newConfigs.length} new search engines.`);
    }

    if (newTasks.length > 0) {
        session.tasks = [...session.tasks, ...newTasks];
        await saveSession(session);
        broadcastSessionStatus(sessionId);
        
        if (session.status === "DONE") {
             session.status = "PAUSED"; 
             await saveSession(session);
             logToSession(sessionId, "ℹ️ New tasks added. Press START to resume.");
        } else if (session.status === "RUNNING") {
             processQueue(sessionId); 
        }
    }
}

async function resetSingleTask(payload) {
    const { sessionId, taskIndex } = payload;
    const session = await getSession(sessionId);
    if (!session) return;

    const task = session.tasks[taskIndex];
    if (task) {
        task.status = "OPEN";         // Re-enable the task
        task.retryCount = 0;          // Reset its attempt counter
        task.pages = [];              // Optional: Clear any partial data from previous fails
        task.totalOrganic = 0;        // Reset count for a clean start
        
        await saveSession(session);   // Persist change to database
        logToSession(sessionId, `🔄 Task Reset: "${task.term}" is back in the queue.`);
        
        // Refresh the UI counts
        broadcastSessionStatus(sessionId);
    }
}

async function removeConfigFromSession(payload) {
    const { sessionId, configIndex } = payload;
    const session = await getSession(sessionId);
    if (!session) return;

    const configToRemove = session.originalConfigs[configIndex];
    if (!configToRemove) return;

    const newConfigs = session.originalConfigs.filter((_, idx) => idx !== configIndex);
    session.originalConfigs = newConfigs;

    let cancelledCount = 0;
    session.tasks.forEach(task => {
        if (task.config.countryCode === configToRemove.countryCode && 
            task.config.langCode === configToRemove.langCode &&
            task.config.domain === configToRemove.domain) {
            
            if (task.status === "OPEN" || task.status === "FAILED") {
                task.status = "CANCELLED";
                cancelledCount++;
            }
        }
    });

    await saveSession(session);
    logToSession(sessionId, `🗑️ Removed Engine: ${configToRemove.countryName}. Cancelled ${cancelledCount} pending tasks.`);
    broadcastSessionStatus(sessionId);
}

async function updateSessionProxies(payload) {
    const { sessionId, useProxies, proxyListStr } = payload;
    const session = await getSession(sessionId);
    if (!session) return;

    let proxyList = [];
    if (useProxies && proxyListStr) {
        proxyList = proxyListStr.split('\n').map(l => l.trim()).filter(l => l.length > 5);
    }

    session.settings.useProxies = useProxies;
    session.settings.proxyList = proxyList;
    
    if (useProxies) {
        await chrome.storage.local.set({ [`proxy_try_${sessionId}`]: 0 });
    } else {
        chrome.proxy.settings.clear({ scope: 'regular' });
        currentProxyAuth = null;
    }

    await saveSession(session);
    logToSession(sessionId, `🛡️ Proxy Settings updated. Active: ${useProxies}, Count: ${proxyList.length}`);
    broadcastSessionStatus(sessionId);
}

async function createNewSession(payload) {
    const { name, queries, configs, resultsLimit, delays, saveSerp, useProxies, proxyListStr } = payload;
    
    let proxyList = [];
    if (useProxies && proxyListStr) {
        proxyList = proxyListStr.split('\n').map(l => l.trim()).filter(l => l.length > 5);
    }

    const id = "sess_" + Date.now();
    const tasks = queries.flatMap(q => configs.map(conf => ({
        term: q, config: conf, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0
    })));
    
    const settings = {
        saveSerp: !!saveSerp,
        useProxies: !!useProxies,
        proxyList: proxyList
    };

    const session = { 
        id, name, status: "OPEN", tasks, currentIndex: 0, globalCount: resultsLimit, delays, settings, originalConfigs: configs, originalQueries: queries
    };
    
    await saveSession(session);
    chrome.runtime.sendMessage({ type: "SESSION_CREATED", payload: { sessionId: id } }).catch(() => { });
}

async function startSession(id) {
    const s = await getSession(id);
    if (!s) return;
    s.status = "RUNNING";
    await chrome.storage.local.set({ [`retry_${id}`]: 0, [`proxy_try_${id}`]: 0 });
    await saveSession(s);
    broadcastSessionStatus(id);
    processQueue(id);
}

async function pauseSession(id, reason = "USER", tabId = null) {
    const s = await getSession(id);
    if (s) {
        if (reason === "USER") cleanupCaptchaHandling(id);
        s.status = reason === "CAPTCHA" ? "PAUSED_CAPTCHA" : "PAUSED";
        await saveSession(s);
        const msg = reason === "CAPTCHA" ? "⚠️ PAUSE: CAPTCHA detected." : "⏸️ PAUSE: Scraper received interrupt signal.";
        logToSession(id, msg, reason === "CAPTCHA" ? "WARN" : "INFO");
        broadcastSessionStatus(id);
        if (reason === "CAPTCHA" && tabId) handleCaptchaEvent(id, tabId);
    }
}

async function deleteSession(id) {
    cleanupCaptchaHandling(id);
    const tx = db.transaction([STORE_SESSIONS, STORE_RESULTS, STORE_LOGS], "readwrite");
    tx.objectStore(STORE_SESSIONS).delete(id);
    await new Promise(r => tx.oncomplete = r);
    broadcastSessionList();
}

async function processQueue(sessionId) {
    let session = await getSession(sessionId);
    if (!session || session.status !== "RUNNING") return;

    const nextIdx = session.tasks.findIndex(t => t.status === "OPEN");
    if (nextIdx === -1) {
        session.status = "DONE";
        await saveSession(session);
        logToSession(sessionId, "🏁 FINISHED: Study completed.");
        broadcastSessionStatus(sessionId);
        return;
    }

    session.currentIndex = nextIdx;
    const currentTask = session.tasks[nextIdx];
    await saveSession(session);

    // Load the engine configuration for the current task
    const engineConfig = await getEngine(currentTask.config.engineId);
    if (!engineConfig) {
        logToSession(sessionId, `❌ ERROR: Plugin for '${currentTask.config.engineId}' not found!`, "ERROR");
        currentTask.status = "FAILED";
        await saveSession(session);
        processQueue(sessionId);
        return;
    }

    let collectedOrganic = currentTask.totalOrganic || 0;
    let currentPage = currentTask.pages.length + 1;

    const existingUrls = new Set();
    currentTask.pages.forEach(p => p.results.organic.forEach(r => existingUrls.add(r.url)));

    logToSession(sessionId, `🚀 TASK START: "${currentTask.term}" using ${engineConfig.engine.name}`);
    broadcastSessionStatus(sessionId);

    let tabId = null;
    try {
        // Load the search page with the correct URL built from the engine config and search term
        const url = buildSearchUrl(currentTask.term, currentTask.config, engineConfig);
        logToSession(sessionId, `🔗 INITIALIZING: ${url}`);

        const tab = await new Promise(r => chrome.tabs.create({ url, active: true }, r));
        tabId = tab.id;

        while (collectedOrganic < session.globalCount && currentPage <= MAX_PAGES) {

            if (await isPaused(sessionId)) break;

            logToSession(sessionId, `🌐 LOADING: Waiting for Page ${currentPage}...`);
            await waitForTabSmart(tabId);

            if (await isPaused(sessionId)) break;
            
            await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] });
            await sleep(getRandomDelay(2000, 4000));

            // Pre-check for CAPTCHA before doing anything on the page
            let preCheck = await chrome.tabs.sendMessage(tabId, { action: "CHECK_CAPTCHA", payload: { config: engineConfig } }).catch(() => null);
            if (preCheck && preCheck.isCaptcha) {
                await handleCaptchaEvent(sessionId, tabId);
                return;
            }

            logToSession(sessionId, `📜 BEHAVIOR: Executing human logic (Page ${currentPage})...`);
            await chrome.tabs.sendMessage(tabId, { action: "SCROLL_AND_PREPARE", payload: { config: engineConfig } }).catch(() => { });
            await sleep(getRandomDelay(3000, 6000));

            if (await isPaused(sessionId)) break;

            // Determine the limit (default to 50 if it's missing)
            const serpLimit = session.settings && session.settings.serpLimit ? session.settings.serpLimit : 50;

            // Only save the SERP if the toggle is on AND we haven't hit the limit for this task yet
            const shouldSaveSerp = session.settings && 
                                (session.settings.saveSerp || session.settings.saveScreenshots || session.settings.saveHtml) && 
                                (currentTask.pages.length < serpLimit);

            let screenshotData = null;
            if (shouldSaveSerp) {
                logToSession(sessionId, "📸 CAPTURING: Full page screenshot...");
                try { screenshotData = await captureFullPage(tabId, engineConfig); } catch (e) { logToSession(sessionId, `⚠️ SCREENSHOT FAILED: ${e}`); }
            }

            if (await isPaused(sessionId)) break;
            
            logToSession(sessionId, "🔍 SCRAPING: Extracting data using plugin rules...");
            const response = await chrome.tabs.sendMessage(tabId, { action: "SCRAPE_SERP", payload: { startRank: collectedOrganic, config: engineConfig } }).catch(() => null);

            if (response && response.isCaptcha) {
                 await handleCaptchaEvent(sessionId, tabId);
                 return;
            }

            if (response && response.data) {
                const data = response.data;
                const newOrganic = data.organic.filter(r => !existingUrls.has(r.url));
                newOrganic.forEach(r => existingUrls.add(r.url));

                const remainingQuota = session.globalCount - collectedOrganic;
                const finalOrganicForPage = newOrganic.slice(0, Math.max(0, remainingQuota));
                data.organic = finalOrganicForPage;

                const aiFound = (data.ai_overview && data.ai_overview.found) ? "YES" : "NO";
                const adsCount = data.ads ? data.ads.length : 0;

                logToSession(sessionId, `📊 P${currentPage}: AI: ${aiFound} | Ads: ${adsCount} | New: ${finalOrganicForPage.length}`);

                let htmlToStore = null;
                if (shouldSaveSerp) {
                    htmlToStore = response.html_content;
                }

                await savePageContent(sessionId, nextIdx, currentPage, { html: htmlToStore, screenshot: screenshotData });
                currentTask.pages.push({ pageNumber: currentPage, results: data });
                
                collectedOrganic += finalOrganicForPage.length;
                currentTask.totalOrganic = collectedOrganic;

                await saveSession(session);

                if (collectedOrganic >= session.globalCount) {
                    logToSession(sessionId, `✅ TARGET MET: Collected ${collectedOrganic}.`);
                    break;
                }

                if (await isPaused(sessionId)) break;

                const nav = await chrome.tabs.sendMessage(tabId, { action: "NAVIGATE_NEXT", payload: { config: engineConfig } });
                
                if (nav && nav.isCaptcha) {
                    await handleCaptchaEvent(sessionId, tabId);
                    return;
                }

                if (!nav || !nav.success) {
                    logToSession(sessionId, "⏹️ END: No more search pages or selector failed.");
                    break;
                }

                currentPage++;
                
                const wait = getRandomDelay(session.delays.min, session.delays.max);
                logToSession(sessionId, `😴 IDLE: Random wait ${Math.round(wait / 1000)}s...`);
                for (let i = 0; i < wait; i += 500) {
                    if (await isPaused(sessionId)) break;
                    await sleep(500);
                }
            } else { throw new Error("Scrape failed (Content Script did not return data)."); }
        }

        const finalCheck = await getSession(sessionId);
        if (finalCheck && finalCheck.status === "RUNNING") {
            currentTask.status = "DONE";
            await saveSession(session);
            logToSession(sessionId, `✔️ TASK COMPLETED: "${currentTask.term}"`);
        }

    } catch (error) {
        logToSession(sessionId, `❌ ERROR: ${error.message}`, "ERROR");
        await handleRetry(sessionId, session, currentTask, error.message);
    } finally {
        const check = await getSession(sessionId);
        if (tabId && (!check || check.status !== "PAUSED_CAPTCHA")) {
             await chrome.tabs.remove(tabId).catch(() => { });
        }
    }

    session = await getSession(sessionId);
    if (session && session.status === "RUNNING") {
        const cooldown = getRandomDelay(5000, 10000);
        logToSession(sessionId, `🍵 COOLDOWN: General break before next task (${Math.round(cooldown / 1000)}s)...`);
        setTimeout(() => processQueue(sessionId), cooldown);
    }
}

// --- 8. UTILITIES ---
function buildSearchUrl(term, taskConfig, engineConfig) {
    // encodeURIComponent wurde hier entfernt, da searchParams das automatisch (und besser) macht!
    const reqData = engineConfig.request;
    
    let u = reqData.baseUrl.replace("{domain}", taskConfig.domain || "");
    const urlObj = new URL(u);
    
    if (reqData.params.query) urlObj.searchParams.set(reqData.params.query, term);
    
    if (reqData.params.country && taskConfig.countryCode) urlObj.searchParams.set(reqData.params.country, taskConfig.countryCode);
    if (reqData.params.language && taskConfig.langCode) urlObj.searchParams.set(reqData.params.language, taskConfig.langCode);
    
    if (reqData.features && reqData.features.requiresUuleEncoding && taskConfig.location) {
        urlObj.searchParams.set(reqData.params.location, generateUule(taskConfig.location));
    }
    
    return urlObj.toString();
}

function generateUule(loc) {
    const secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    return `w+CAIQICI${secret[loc.length % 65]}${btoa(loc)}`;
}

async function captureFullPage(tabId, engineConfig) {
    return new Promise((resolve, reject) => {
        try {
            chrome.debugger.attach({ tabId }, "1.3", () => {
                if (chrome.runtime.lastError) return reject(chrome.runtime.lastError.message);
                
                chrome.tabs.sendMessage(tabId, { action: "GET_DIMENSIONS", payload: { config: engineConfig } }, (m) => {
                    if (chrome.runtime.lastError) {
                        console.warn("RAT: GET_DIMENSIONS failed, using fallback metrics.", chrome.runtime.lastError.message);
                    }
                    
                    const width = m?.width || 1920;
                    const height = m?.height || 5000;
                    
                    setTimeout(() => {
                        chrome.debugger.sendCommand({ tabId }, "Page.captureScreenshot", { 
                            format: "jpeg", 
                            quality: 100, 
                            fromSurface: true, 
                            captureBeyondViewport: true 
                        }, (res) => {
                            chrome.debugger.detach({ tabId }).catch(() => {});
                            if (chrome.runtime.lastError) return reject(chrome.runtime.lastError.message);
                            if (res?.data) resolve("data:image/jpeg;base64," + res.data);
                            else reject("No image data received");
                        });
                    }, 500);
                });
            });
        } catch (error) {
            reject(error.message);
        }
    });
}

function waitForTabSmart(tabId) {
    return new Promise(r => {
        chrome.tabs.get(tabId, t => {
            if (t.status === 'complete') r();
            else {
                const l = (id, chg) => {
                    if (id === tabId && chg.status === 'complete') {
                        chrome.tabs.onUpdated.removeListener(l);
                        r();
                    }
                };
                chrome.tabs.onUpdated.addListener(l);
            }
        });
    });
}

async function handleRetry(sessionId, session, task, errorMsg) {
    if (await isPaused(sessionId)) return;

    task.retryCount++;
    
    if (task.retryCount > 3) {
        task.status = "FAILED";
        logToSession(sessionId, `💀 FAILED: Abandoning after 3 retries. Error: ${errorMsg}`, "ERROR");
    } else {
        logToSession(sessionId, `⚠️ RETRY ${task.retryCount}/3 in 5s... Reason: ${errorMsg}`, "WARN");
        task.status = "OPEN";
    }

    // CRITICAL FIX: The database must be updated here!
    await saveSession(session); 
    await sleep(5000);
}

async function broadcastSessionList() {
    const sessions = await getAllSessions();
    const list = sessions.map(s => ({
        id: s.id,
        name: s.name,
        status: s.status,
        progress: {
            done: s.tasks.filter(t => t.status === "DONE").length,
            total: s.tasks.length
        }
    }));
    chrome.runtime.sendMessage({ type: "SESSION_LIST", payload: list }).catch(() => { });
}

async function broadcastSessionStatus(id) {
    const s = await getSession(id);
    if (!s) return;
    const logs = await getLogs(id);
    const current = s.tasks[s.currentIndex];
    
    chrome.runtime.sendMessage({
        type: "SESSION_STATUS",
        payload: {
            sessionId: id,
            name: s.name,
            status: s.status,
            progress: {
                done: s.tasks.filter(t => t.status === "DONE").length,
                total: s.tasks.length
            },
            currentQuery: current ? `${current.term} (${current.config.engineName})` : "Done",
            logs: logs || [],
            delays: s.delays,
            originalConfigs: s.originalConfigs,
            originalQueries: s.originalQueries,
            settings: s.settings,
            globalCount: s.globalCount
        }
    }).catch(() => { });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function getRandomDelay(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

async function updateSessionDelay(payload) {
    const s = await getSession(payload.sessionId);
    if (s) {
        s.delays = { min: payload.min * 1000, max: payload.max * 1000 };
        await saveSession(s);
        logToSession(payload.sessionId, `⏱️ Delay updated to ${payload.min}-${payload.max}s`);
        broadcastSessionStatus(payload.sessionId);
    }
}

async function updateSessionLimit(payload) {
    const s = await getSession(payload.sessionId);
    if (s) {
        s.globalCount = parseInt(payload.limit);
        await saveSession(s);
        logToSession(payload.sessionId, `🎯 Target Results updated to ${s.globalCount}`);
        broadcastSessionStatus(payload.sessionId);
    }
}

async function updateSessionStorageSettings(payload) {
    const { sessionId, saveSerp, serpLimit } = payload;
    const session = await getSession(sessionId);
    if (!session) return;

    if (!session.settings) session.settings = {};
    session.settings.saveSerp = !!saveSerp;
    if (serpLimit !== undefined) session.settings.serpLimit = serpLimit; // NEW: Save the limit
    session.settings.saveScreenshots = false; 
    session.settings.saveHtml = false;

    await saveSession(session);
    logToSession(sessionId, `💾 Storage Settings updated. Save SERP: ${!!saveSerp}, Limit: ${session.settings.serpLimit}`);
    broadcastSessionStatus(sessionId);
}