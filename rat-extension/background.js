/**
 * @file background.js - Version 2.2 (Unattended Edition)
 * Core Service Worker for the Result Assessment Tool (RAT).
 * Handles persistence (IndexedDB), proxy rotation, the scraping runner and unattended operation
 * (keepalive, watchdog, crash recovery, captcha back-off, webhooks, recurring studies).
 */

importScripts('lib/proxy.js', 'lib/human.js');

// --- 1. CONFIGURATION & STATE ---
const DB_NAME = "RAT_Database";
const STORE_SESSIONS = "sessions";
const STORE_RESULTS = "results";
const STORE_LOGS = "logs";
const STORE_ENGINES = "engines";
const MAX_PAGES = 100;

const RETRY_DELAYS = [5, 15, 30, 60];
const WATCHDOG_ALARM = "rat_watchdog";
let activeCaptchaListeners = {};
let db;

const DEFAULT_BEHAVIOR = {
    humanPacing: true,
    shuffle: false,
    typedSearch: false,
    trustedInput: true,
    breakEvery: 0,
    breakMinSec: 120,
    breakMaxSec: 300
};

function getSettings(session) {
    const raw = (session && session.settings) || {};
    const s = Object.assign({
        saveSerp: false, serpLimit: 100,
        useProxies: false, proxyList: [], proxyMode: "list", proxyUsernameTemplate: "",
        proxyBudget: 0, proxyCooldownMin: 120, clearCookiesOnRotate: true,
        webhookUrl: "", repeatEveryHours: 0, repeatTimes: 0, maxCaptchaRounds: 10
    }, raw);
    s.behavior = Object.assign({}, DEFAULT_BEHAVIOR, raw.behavior || {});
    return s;
}

function ensureMetrics(m) {
    return Object.assign({
        pages: 0, results: 0, zeroPages: 0, captchas: 0, tasksDone: 0, tasksFailed: 0,
        rotations: 0, zeroStreak: 0, failStreak: 0, tasksSinceBreak: 0, byVariant: {}, startedAt: Date.now()
    }, m || {});
}

function variantKey(cfg) {
    return `${cfg.engineName || cfg.engineId}|${cfg.countryCode || ""}|${cfg.langCode || ""}`;
}

// --- 2. INITIALIZATION (DB & ENGINES) ---
async function initDB() {
    if (db) return;
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 8);

        request.onupgradeneeded = (event) => {
            const d = event.target.result;
            if (!d.objectStoreNames.contains(STORE_SESSIONS)) d.createObjectStore(STORE_SESSIONS, { keyPath: "id" });
            if (!d.objectStoreNames.contains(STORE_RESULTS)) d.createObjectStore(STORE_RESULTS);
            if (!d.objectStoreNames.contains(STORE_LOGS)) d.createObjectStore(STORE_LOGS, { autoIncrement: true });
            if (!d.objectStoreNames.contains(STORE_ENGINES)) d.createObjectStore(STORE_ENGINES, { keyPath: "engine.id" });
        };

        request.onsuccess = async (event) => {
            db = event.target.result;
            db.onversionchange = () => { db.close(); db = null; };
            await syncDefaultEngines();
            resolve();
        };

        request.onerror = (event) => {
            console.error("Database error: " + event.target.errorCode);
            reject("DB Error");
        };
    });
}

async function syncDefaultEngines() {
    let engineFilesToLoad = [];

    try {
        const indexUrl = chrome.runtime.getURL('engines/index.json');
        const indexResponse = await fetch(indexUrl);
        if (!indexResponse.ok) throw new Error("index.json not found");
        engineFilesToLoad = await indexResponse.json();
    } catch (err) {
        console.error("❌ Could not load engines/index.json:", err);
        return;
    }

    const enginesToSave = [];
    for (const fileName of engineFilesToLoad) {
        try {
            const response = await fetch(chrome.runtime.getURL(`engines/${fileName}`));
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            enginesToSave.push(await response.json());
        } catch (err) {
            console.error(`❌ Error loading ${fileName}:`, err);
        }
    }

    if (enginesToSave.length === 0) return;

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_ENGINES, "readwrite");
        const store = tx.objectStore(STORE_ENGINES);
        enginesToSave.forEach(engine => store.put(engine));
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
        const req = db.transaction(STORE_ENGINES, "readonly").objectStore(STORE_ENGINES).get(id);
        req.onsuccess = () => r(req.result);
        req.onerror = () => r(null);
    });
}

async function getAllEngines() {
    if (!db) await initDB();
    return new Promise(r => {
        const req = db.transaction(STORE_ENGINES, "readonly").objectStore(STORE_ENGINES).getAll();
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
    db.transaction(STORE_LOGS, "readwrite").objectStore(STORE_LOGS).add(entry);
    chrome.runtime.sendMessage({ type: "LOG_ENTRY", payload: { sessionId, entry } }).catch(() => { });
}

/** Newest `limit` log lines of one session (reverse cursor, stops early). */
async function getLogs(sessionId, limit = 400) {
    if (!db) await initDB();
    return new Promise(resolve => {
        const out = [];
        const req = db.transaction(STORE_LOGS, "readonly").objectStore(STORE_LOGS).openCursor(null, "prev");
        req.onsuccess = () => {
            const c = req.result;
            if (!c || out.length >= limit) return resolve(out.reverse());
            if (c.value.sessionId === sessionId) out.push(c.value);
            c.continue();
        };
        req.onerror = () => resolve(out.reverse());
    });
}

// --- 4. DATA HELPERS ---
async function saveSession(session) {
    if (!db) await initDB();
    const tx = db.transaction(STORE_SESSIONS, "readwrite");
    tx.objectStore(STORE_SESSIONS).put(session);
    return new Promise((r, rej) => { tx.oncomplete = r; tx.onerror = () => rej(tx.error); });
}

async function getSession(id) {
    if (!db) await initDB();
    return new Promise(r => {
        const req = db.transaction(STORE_SESSIONS, "readonly").objectStore(STORE_SESSIONS).get(id);
        req.onsuccess = () => r(req.result);
        req.onerror = () => r(undefined);
    });
}

async function getAllSessions() {
    if (!db) await initDB();
    return new Promise(r => {
        const req = db.transaction(STORE_SESSIONS, "readonly").objectStore(STORE_SESSIONS).getAll();
        req.onsuccess = () => r(req.result);
    });
}

/** Serialised read-modify-write of one session. The mutator may return false to skip the write. */
const sessionLocks = new Map();
function updateSession(id, mutator) {
    const prev = sessionLocks.get(id) || Promise.resolve();
    const next = prev.catch(() => { }).then(async () => {
        const s = await getSession(id);
        if (!s) return null;
        const r = await mutator(s);
        if (r === false) return s;
        await saveSession(s);
        return s;
    });
    sessionLocks.set(id, next);
    next.catch(() => { }).then(() => { if (sessionLocks.get(id) === next) sessionLocks.delete(id); });
    return next;
}

/** Writes the runner's working copy of one task back without touching the rest of the session. */
async function persistTask(sessionId, idx, task) {
    let cancelled = false;
    await updateSession(sessionId, s => {
        const cur = s.tasks[idx];
        if (!cur) return false;
        if (cur.status === "CANCELLED" && task.status !== "CANCELLED") { cancelled = true; return false; }
        s.tasks[idx] = task;
    });
    return !cancelled;
}

async function savePageContent(sessionId, taskIdx, pageNum, content) {
    const tx = db.transaction(STORE_RESULTS, "readwrite");
    tx.objectStore(STORE_RESULTS).put(content, `${sessionId}_${taskIdx}_${pageNum}`);
    return new Promise((r, rej) => { tx.oncomplete = r; tx.onerror = () => rej(tx.error); });
}

async function isPaused(sessionId) {
    const s = await getSession(sessionId);
    return (!s || (s.status !== "RUNNING"));
}

// --- 5. WEBHOOK NOTIFICATIONS ---
const lastNotify = new Map();
async function notify(sessionId, event, text, minGapMs = 0) {
    try {
        const s = await getSession(sessionId);
        if (!s) return;
        const url = getSettings(s).webhookUrl;
        if (!url || !/^https?:\/\//i.test(url)) return;
        const key = sessionId + ":" + event;
        if (minGapMs && Date.now() - (lastNotify.get(key) || 0) < minGapMs) return;
        lastNotify.set(key, Date.now());
        const msg = `[RAT] ${s.name}: ${text}`;
        await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                event, text: msg, content: msg,
                session: { id: s.id, name: s.name, status: s.status, done: s.tasks.filter(t => t.status === "DONE").length, total: s.tasks.length },
                ts: new Date().toISOString()
            })
        });
    } catch (e) {
        logToSession(sessionId, `⚠️ Webhook failed: ${e.message}`, "WARN");
    }
}

// --- 6. ROUTING ---
chrome.runtime.onInstalled.addListener(async () => {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => { });
    await initDB();
    await clearProxyConfig();
    ensureWatchdogAlarm();
});

chrome.runtime.onStartup.addListener(async () => {
    await initDB();
    ensureWatchdogAlarm();
    watchdog();
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (!msg || !msg.action) return false;
    handleMessage(msg).then(sendResponse).catch(e => sendResponse({ error: e && e.message || String(e) }));
    return true;
});

async function handleMessage(msg) {
    if (!db) await initDB();
    const p = msg.payload || {};
    switch (msg.action) {
        case "GET_SESSIONS":
        case "REFRESH_SESSIONS": broadcastSessionList(); break;
        case "CREATE_SESSION": return await createNewSession(p);
        case "GET_SESSION_STATUS": if (p.sessionId) broadcastSessionStatus(p.sessionId, true); break;
        case "START": if (p.sessionId) await startSession(p.sessionId); break;
        case "PAUSE": if (p.sessionId) await pauseSession(p.sessionId); break;
        case "DELETE_SESSION": if (p.sessionId) await deleteSession(p.sessionId); break;
        case "UPDATE_DELAY": await updateSessionDelay(p); break;
        case "UPDATE_LIMIT": await updateSessionLimit(p); break;
        case "ADD_ITEMS": await addItemsToSession(p); break;
        case "UPDATE_PROXIES": return await updateSessionProxies(p);
        case "UPDATE_BEHAVIOR": return await updateSessionBehavior(p);
        case "VALIDATE_PROXIES": return validateProxyLines(p.lines || []);
        case "TEST_PROXIES": return await runProxyTest(p);
        case "REMOVE_CONFIG": await removeConfigFromSession(p); break;
        case "GET_TASKS": broadcastSessionTasks(p.sessionId); break;
        case "REMOVE_TASK": await removeSingleTask(p); break;
        case "UPDATE_STORAGE_SETTINGS": await updateSessionStorageSettings(p); break;
        case "GET_ENGINES": broadcastEngines(); break;
        case "SAVE_ENGINE": await saveEngine(p); broadcastEngines(); break;
        case "DELETE_ENGINE": await deleteEngine(p.id); broadcastEngines(); break;
        case "RESET_TASK": if (p.sessionId) await resetSingleTask(p); break;
    }
    return { ok: true };
}

async function broadcastEngines() {
    const engines = await getAllEngines();
    chrome.runtime.sendMessage({ type: "ENGINE_LIST", payload: engines }).catch(() => { });
}

// --- 7. RUNNER INFRASTRUCTURE (lock, keepalive, watchdog, recovery) ---
const runners = new Set();
const pendingKick = new Set();
let keepAliveTimer = null;

function startKeepAlive() {
    if (keepAliveTimer) return;
    try { chrome.power.requestKeepAwake("system"); } catch (e) { }
    keepAliveTimer = setInterval(() => { chrome.runtime.getPlatformInfo(() => { void chrome.runtime.lastError; }); }, 20000);
}

function stopKeepAliveIfIdle() {
    if (runners.size > 0 || !keepAliveTimer) return;
    clearInterval(keepAliveTimer);
    keepAliveTimer = null;
    try { chrome.power.releaseKeepAwake(); } catch (e) { }
}

/** Starts the runner for a session unless one is already active in this service-worker instance. */
function kick(sessionId) {
    if (runners.has(sessionId)) { pendingKick.add(sessionId); return; }
    runners.add(sessionId);
    startKeepAlive();
    runSession(sessionId)
        .catch(e => logToSession(sessionId, `❌ Runner crashed: ${e && e.message || e}`, "ERROR"))
        .finally(async () => {
            runners.delete(sessionId);
            stopKeepAliveIfIdle();
            if (pendingKick.delete(sessionId)) kick(sessionId);
            await releaseProxyIfIdle();
            await startNextQueued();
        });
}

async function runSession(sessionId) {
    while (true) {
        const result = await processNextTask(sessionId);
        if (result === "stop") return;

        const s = await getSession(sessionId);
        if (!s || s.status !== "RUNNING") return;
        const st = getSettings(s);
        const human = st.behavior.humanPacing;

        let gap;
        if (result === "fast") gap = pacedDelay(4000, 9000, human);
        else if (human) gap = pacedDelay(Math.max(5000, s.delays.min * 0.5), Math.max(10000, s.delays.max * 0.8), true);
        else gap = rndInt(5000, 10000);

        const m = ensureMetrics(s.metrics);
        if (st.behavior.breakEvery > 0 && m.tasksSinceBreak >= st.behavior.breakEvery) {
            gap = rndInt(st.behavior.breakMinSec, Math.max(st.behavior.breakMinSec, st.behavior.breakMaxSec)) * 1000;
            await updateSession(sessionId, x => { x.metrics = ensureMetrics(x.metrics); x.metrics.tasksSinceBreak = 0; });
            logToSession(sessionId, `☕ BREAK: Longer pause (${Math.round(gap / 1000)}s) after ${m.tasksSinceBreak} tasks.`);
        } else {
            logToSession(sessionId, `🍵 COOLDOWN: Break before next task (${Math.round(gap / 1000)}s)...`);
        }
        if (!(await sleepWhileRunning(sessionId, gap))) return;
    }
}

async function sleepWhileRunning(sessionId, ms) {
    for (let waited = 0; waited < ms; waited += 1000) {
        if (await isPaused(sessionId)) return false;
        await sleep(Math.min(1000, ms - waited));
    }
    return !(await isPaused(sessionId));
}

/** Only one study scrapes at a time (one browser, one global proxy). Others wait as QUEUED. */
async function requestRun(sessionId) {
    const all = await getAllSessions();
    const busy = all.some(x => x.id !== sessionId && x.status === "RUNNING");
    await updateSession(sessionId, s => { s.status = busy ? "QUEUED" : "RUNNING"; });
    if (busy) logToSession(sessionId, "⏳ Another study is running. This study is queued and starts automatically.");
    broadcastSessionStatus(sessionId);
    if (!busy) kick(sessionId);
}

async function startNextQueued() {
    const all = await getAllSessions();
    if (all.some(x => x.status === "RUNNING")) return;
    const next = all.find(x => x.status === "QUEUED");
    if (next) {
        await updateSession(next.id, s => { s.status = "RUNNING"; });
        logToSession(next.id, "▶️ Queue: starting this study now.");
        broadcastSessionStatus(next.id);
        kick(next.id);
    }
}

async function releaseProxyIfIdle() {
    if (!(await proxyIsActive())) return;
    const all = await getAllSessions();
    if (all.some(x => x.status === "RUNNING" || x.status === "PAUSED_CAPTCHA")) return;
    await clearProxyConfig();
}

function ensureWatchdogAlarm() {
    chrome.alarms.get(WATCHDOG_ALARM, (a) => {
        if (!a) chrome.alarms.create(WATCHDOG_ALARM, { delayInMinutes: 1, periodInMinutes: 1 });
    });
}

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === WATCHDOG_ALARM) watchdog();
});

let watchdogBusy = false;
async function watchdog() {
    if (watchdogBusy) return;
    watchdogBusy = true;
    try {
        if (!db) await initDB();
        const now = Date.now();
        const sessions = await getAllSessions();
        for (const s of sessions) {
            if (s.status === "RUNNING" && !runners.has(s.id)) {
                logToSession(s.id, "♻️ RECOVERY: Runner was not active (browser/worker restart). Resuming study...", "WARN");
                kick(s.id);
            } else if (s.status === "PAUSED_CAPTCHA") {
                if (s.retryAt && s.retryAt <= now) {
                    logToSession(s.id, "⏰ Retry time reached. Resuming after captcha pause...");
                    await resumeAfterCaptcha(s.id, false);
                } else if (s.captchaTabId && !activeCaptchaListeners[s.id]) {
                    watchCaptchaTab(s.id, s.captchaTabId);
                }
            } else if (s.status === "DONE" && s.nextRunAt && s.nextRunAt <= now) {
                await spawnNextRun(s);
            }
        }
        await startNextQueued();
    } catch (e) {
        console.error("watchdog error", e);
    } finally {
        watchdogBusy = false;
    }
}

// --- 8. CAPTCHA / BLOCK HANDLING ---
function engineCookieDomainsFor(engine, cfgs) {
    const set = new Set();
    for (const c of cfgs) {
        try { set.add(new URL(engine.request.baseUrl.replace("{domain}", c.domain || "")).hostname.replace(/^www\./, "")); } catch (e) { }
    }
    (engine.request.cookieDomains || []).forEach(d => set.add(d));
    return set;
}

async function sessionCookieDomains(session) {
    const out = new Set();
    for (const id of new Set((session.originalConfigs || []).map(c => c.engineId))) {
        const e = await getEngine(id);
        if (!e) continue;
        engineCookieDomainsFor(e, session.originalConfigs.filter(c => c.engineId === id)).forEach(d => out.add(d));
    }
    return [...out];
}

/**
 * Called when a captcha is detected. Returns "rotated" (task can be retried at once with a new IP),
 * "waiting" (back-off scheduled) or "stopped".
 */
async function handleCaptchaEvent(sessionId, tabId, taskInfo) {
    const s0 = await getSession(sessionId);
    if (!s0 || s0.status !== "RUNNING") return "stopped";
    const settings = getSettings(s0);
    const log = (m, l) => logToSession(sessionId, m, l);

    let rounds = 0;
    await updateSession(sessionId, s => {
        const m = s.metrics = ensureMetrics(s.metrics);
        m.captchas++;
        const t = s.tasks[taskInfo && taskInfo.idx];
        if (t) {
            const v = m.byVariant[variantKey(t.config)] || (m.byVariant[variantKey(t.config)] = { pages: 0, results: 0, zeroPages: 0, captchas: 0, ai: 0, ads: 0 });
            v.captchas = (v.captchas || 0) + 1;
        }
        s.captchaRounds = (s.captchaRounds || 0) + 1;
        rounds = s.captchaRounds;
    });
    log(`🛡️ CAPTCHA detected (consecutive: ${rounds}).`, "WARN");

    if (rounds > settings.maxCaptchaRounds) {
        await closeTab(tabId);
        await pauseForAttention(sessionId, `Too many captchas in a row (${rounds - 1}). The study was paused so you can check proxies/settings.`);
        return "stopped";
    }

    const hasProxies = settings.useProxies && parseProxyList(settings.proxyList).entries.length > 0;
    if (hasProxies) {
        const r = await proxyRotate({ sessionId, settings, reason: "captcha", log, cookieDomains: await sessionCookieDomains(s0) });
        if (r.rotated) {
            await updateSession(sessionId, s => { const m = s.metrics = ensureMetrics(s.metrics); m.rotations++; });
            await closeTab(tabId);
            notify(sessionId, "captcha", `Captcha detected, switched IP (round ${rounds}).`, 10 * 60000);
            return "rotated";
        }
        log("⚠️ All proxies are cooling down after captchas.", "WARN");
    }

    let waitMin = RETRY_DELAYS[Math.min(rounds - 1, RETRY_DELAYS.length - 1)];
    if (hasProxies) {
        const until = await proxyMinutesUntilAvailable(sessionId, settings);
        if (until > 0) waitMin = Math.max(waitMin, until);
    }
    waitMin = Math.max(1, Math.round(waitMin * rndFloat(0.85, 1.25)));
    await enterWaitMode(sessionId, tabId, waitMin);
    notify(sessionId, "captcha", `Captcha detected, no fresh IP available. Waiting ${waitMin} min before retrying (round ${rounds}).`, 10 * 60000);
    return "waiting";
}

async function enterWaitMode(sessionId, tabId, waitMinutes, reason) {
    await updateSession(sessionId, s => {
        s.status = "PAUSED_CAPTCHA";
        s.retryAt = Date.now() + waitMinutes * 60000;
        s.captchaTabId = tabId || null;
    });
    if (reason) logToSession(sessionId, `⏸️ ${reason}`, "WARN");
    logToSession(sessionId, `🛡️ Automation paused. Automatic retry in ${waitMinutes} minutes (or solve the captcha manually in the open tab).`, "WARN");
    broadcastSessionStatus(sessionId);
    cleanupCaptchaHandling(sessionId);
    if (tabId) watchCaptchaTab(sessionId, tabId);
}

function watchCaptchaTab(sessionId, tabId) {
    cleanupCaptchaHandling(sessionId);
    const onTabUpdated = async (updatedTabId, changeInfo, tab) => {
        if (updatedTabId !== tabId || changeInfo.status !== "complete") return;
        const currentUrl = (tab.url || "").toLowerCase();
        if (currentUrl.includes("sorry") || currentUrl.includes("captcha") || onTabUpdated.isResolving) return;
        onTabUpdated.isResolving = true;
        try {
            await sleep(1500);
            const s = await getSession(sessionId);
            if (!s || s.status !== "PAUSED_CAPTCHA") return;
            const task = s.tasks[s.currentIndex];
            const engineConfig = task ? await getEngine(task.config.engineId) : null;
            let check = await sendToTab(tabId, { action: "CHECK_CAPTCHA", payload: { config: engineConfig } }, 8000);
            if (!check) {
                await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] }).catch(() => { });
                await sleep(500);
                check = await sendToTab(tabId, { action: "CHECK_CAPTCHA", payload: { config: engineConfig } }, 8000);
            }
            if (check && !check.isCaptcha) {
                logToSession(sessionId, "✅ Captcha solved manually. Continuing...", "SUCCESS");
                await resumeAfterCaptcha(sessionId, true);
            }
        } catch (e) { /* keep waiting */ }
        finally { onTabUpdated.isResolving = false; }
    };
    chrome.tabs.onUpdated.addListener(onTabUpdated);
    activeCaptchaListeners[sessionId] = onTabUpdated;
}

function cleanupCaptchaHandling(sessionId) {
    if (activeCaptchaListeners[sessionId]) {
        chrome.tabs.onUpdated.removeListener(activeCaptchaListeners[sessionId]);
        delete activeCaptchaListeners[sessionId];
    }
}

async function resumeAfterCaptcha(sessionId, manual) {
    cleanupCaptchaHandling(sessionId);
    const s = await getSession(sessionId);
    if (!s || s.status !== "PAUSED_CAPTCHA") return;
    if (s.captchaTabId) await closeTab(s.captchaTabId);
    if (manual) await proxyClearCurrentCooldown(sessionId, getSettings(s));
    await updateSession(sessionId, x => {
        x.retryAt = null; x.captchaTabId = null;
        if (manual) x.captchaRounds = 0;
    });
    await requestRun(sessionId);
}

async function pauseForAttention(sessionId, text) {
    cleanupCaptchaHandling(sessionId);
    await updateSession(sessionId, s => { s.status = "PAUSED"; s.retryAt = null; });
    logToSession(sessionId, `🛑 ATTENTION: ${text}`, "ERROR");
    broadcastSessionStatus(sessionId);
    await notify(sessionId, "attention", text);
}

async function closeTab(tabId) {
    if (!tabId) return;
    try { await chrome.tabs.remove(tabId); } catch (e) { }
}

// --- 9. SESSION MANAGEMENT ---
async function broadcastSessionTasks(sessionId) {
    const session = await getSession(sessionId);
    if (!session) return;

    const simplifiedTasks = session.tasks.map((t, index) => ({
        index: index,
        term: t.term,
        engine: t.config.engineName || "Unknown",
        country: t.config.countryCode,
        lang: t.config.langCode,
        status: t.status,
        retryCount: t.retryCount
    }));

    chrome.runtime.sendMessage({
        type: "TASK_LIST_UPDATE",
        payload: { sessionId, tasks: simplifiedTasks }
    }).catch(() => { });
}

async function removeSingleTask(payload) {
    const { sessionId, taskIndex } = payload;
    let blocked = false;
    await updateSession(sessionId, s => {
        const task = s.tasks[taskIndex];
        if (!task) return false;
        if (task.status === "DONE") { blocked = true; return false; }
        task.status = "CANCELLED";
    });
    if (blocked) logToSession(sessionId, "⚠️ Cannot remove completed task.", "WARN");
    broadcastSessionStatus(sessionId);
    broadcastSessionTasks(sessionId);
}

async function addItemsToSession(payload) {
    const { sessionId, newQueries, newConfigs } = payload;
    let added = 0;
    let finalStatus = null;

    await updateSession(sessionId, session => {
        let newTasks = [];
        const mk = (q, conf) => ({ term: q, config: conf, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0 });

        if (newQueries && newQueries.length > 0) {
            newTasks = newTasks.concat(newQueries.flatMap(q => session.originalConfigs.map(conf => mk(q, conf))));
            session.originalQueries = [...session.originalQueries, ...newQueries];
            logToSession(sessionId, `➕ Added ${newQueries.length} new queries.`);
        }
        if (newConfigs && newConfigs.length > 0) {
            newTasks = newTasks.concat(session.originalQueries.flatMap(q => newConfigs.map(conf => mk(q, conf))));
            session.originalConfigs = [...session.originalConfigs, ...newConfigs];
            logToSession(sessionId, `➕ Added ${newConfigs.length} new search engines.`);
        }
        if (newTasks.length === 0) return false;
        session.tasks = [...session.tasks, ...newTasks];
        added = newTasks.length;
        if (session.status === "DONE") {
            session.status = "PAUSED";
            session.nextRunAt = null;
            logToSession(sessionId, "ℹ️ New tasks added. Press START to resume.");
        }
        finalStatus = session.status;
    });

    if (added > 0) {
        broadcastSessionStatus(sessionId);
        if (finalStatus === "RUNNING") kick(sessionId);
    }
}

async function resetSingleTask(payload) {
    const { sessionId, taskIndex } = payload;
    let term = null;
    await updateSession(sessionId, session => {
        const task = session.tasks[taskIndex];
        if (!task) return false;
        task.status = "OPEN";
        task.retryCount = 0;
        task.pages = [];
        task.totalOrganic = 0;
        task.resume = null;
        term = task.term;
    });
    if (term !== null) {
        logToSession(sessionId, `🔄 Task Reset: "${term}" is back in the queue.`);
        broadcastSessionStatus(sessionId);
    }
}

async function removeConfigFromSession(payload) {
    const { sessionId, configIndex } = payload;
    let label = null, cancelledCount = 0;
    await updateSession(sessionId, session => {
        const configToRemove = session.originalConfigs[configIndex];
        if (!configToRemove) return false;
        session.originalConfigs = session.originalConfigs.filter((_, idx) => idx !== configIndex);
        session.tasks.forEach(task => {
            if (task.config.engineId === configToRemove.engineId &&
                task.config.countryCode === configToRemove.countryCode &&
                task.config.langCode === configToRemove.langCode &&
                task.config.domain === configToRemove.domain &&
                (task.config.location || '') === (configToRemove.location || '')) {
                if (task.status === "OPEN" || task.status === "FAILED") { task.status = "CANCELLED"; cancelledCount++; }
            }
        });
        label = configToRemove.countryName;
    });
    if (label !== null) {
        logToSession(sessionId, `🗑️ Removed Engine: ${label}. Cancelled ${cancelledCount} pending tasks.`);
        broadcastSessionStatus(sessionId);
    }
}

function proxyLinesFromString(str) {
    return (str || "").split("\n").map(l => l.trim()).filter(l => l.length > 0);
}

function validateProxyLines(lines) {
    const { entries, errors } = parseProxyList(lines);
    return {
        valid: entries.length,
        errors: errors.map(x => ({ line: x.raw.replace(/:[^:@]*@/, ":***@").replace(/^([^:]+:[^:]+:[^:]+):.*$/, "$1:***"), error: x.error }))
    };
}

function applyProxySettingsToObject(settings, payload) {
    if (payload.proxyMode) settings.proxyMode = payload.proxyMode === "gateway" ? "gateway" : "list";
    if (payload.proxyUsernameTemplate !== undefined) settings.proxyUsernameTemplate = (payload.proxyUsernameTemplate || "").trim();
    if (payload.proxyBudget !== undefined) settings.proxyBudget = Math.max(0, parseInt(payload.proxyBudget, 10) || 0);
    if (payload.proxyCooldownMin !== undefined) settings.proxyCooldownMin = Math.max(1, parseInt(payload.proxyCooldownMin, 10) || 120);
    if (payload.clearCookiesOnRotate !== undefined) settings.clearCookiesOnRotate = !!payload.clearCookiesOnRotate;
}

async function updateSessionProxies(payload) {
    const { sessionId, useProxies, proxyListStr } = payload;
    const lines = useProxies ? proxyLinesFromString(proxyListStr) : [];
    const validation = validateProxyLines(lines);

    const s = await updateSession(sessionId, session => {
        session.settings = session.settings || {};
        session.settings.useProxies = !!useProxies;
        session.settings.proxyList = lines;
        applyProxySettingsToObject(session.settings, payload);
    });
    if (!s) return { error: "Study not found" };

    await resetProxyState(sessionId);
    if (!useProxies && s.status !== "RUNNING" && s.status !== "PAUSED_CAPTCHA") await clearProxyConfig();

    logToSession(sessionId, `🛡️ Proxy settings updated. Active: ${!!useProxies}, usable entries: ${validation.valid}, invalid lines: ${validation.errors.length}`);
    validation.errors.forEach(e => logToSession(sessionId, `⚠️ Proxy line ignored (${e.error}): ${e.line}`, "WARN"));
    broadcastSessionStatus(sessionId);
    return validation;
}

async function updateSessionBehavior(payload) {
    const { sessionId } = payload;
    let webhookWarning = null;
    const s = await updateSession(sessionId, session => {
        session.settings = session.settings || {};
        const st = session.settings;
        st.behavior = Object.assign({}, DEFAULT_BEHAVIOR, st.behavior || {});
        const b = payload.behavior || {};
        ["humanPacing", "shuffle", "typedSearch", "trustedInput"].forEach(k => { if (b[k] !== undefined) st.behavior[k] = !!b[k]; });
        ["breakEvery", "breakMinSec", "breakMaxSec"].forEach(k => { if (b[k] !== undefined) st.behavior[k] = Math.max(0, parseInt(b[k], 10) || 0); });
        if (payload.webhookUrl !== undefined) {
            const u = (payload.webhookUrl || "").trim();
            if (u && !/^https?:\/\/[^\s]+$/i.test(u)) { webhookWarning = "Webhook URL must start with http:// or https://"; st.webhookUrl = ""; }
            else st.webhookUrl = u;
        }
        if (payload.repeatEveryHours !== undefined) st.repeatEveryHours = Math.max(0, parseFloat(payload.repeatEveryHours) || 0);
        if (payload.repeatTimes !== undefined) st.repeatTimes = Math.max(0, parseInt(payload.repeatTimes, 10) || 0);
        if (payload.maxCaptchaRounds !== undefined) st.maxCaptchaRounds = Math.max(1, parseInt(payload.maxCaptchaRounds, 10) || 10);
        if (session.status === "DONE") {
            session.nextRunAt = (st.repeatEveryHours > 0 && st.repeatTimes > 0) ? Date.now() + st.repeatEveryHours * 3600000 : null;
        }
    });
    if (!s) return { error: "Study not found" };
    logToSession(sessionId, "⚙️ Behavior & unattended settings updated.");
    broadcastSessionStatus(sessionId);
    return { ok: true, warning: webhookWarning };
}

async function runProxyTest(payload) {
    const all = await getAllSessions();
    if (all.some(x => x.status === "RUNNING")) return { error: "A study is currently running. Pause it before testing proxies (the proxy setting is shared by the whole browser)." };
    const lines = proxyLinesFromString(payload.proxyListStr);
    const settings = {
        proxyList: lines,
        proxyMode: payload.proxyMode === "gateway" ? "gateway" : "list",
        proxyUsernameTemplate: (payload.proxyUsernameTemplate || "").trim(),
        webhookUrl: payload.webhookUrl || ""
    };
    const id = payload.sessionId || "__test__";
    const r = await testProxies({ sessionId: id, settings });
    if (id === "__test__") await resetProxyState(id);
    return r;
}

async function createNewSession(payload) {
    const { name, queries, configs, resultsLimit, limitType, delays, saveSerp, serpLimit, useProxies } = payload;
    const lines = useProxies ? proxyLinesFromString(payload.proxyListStr) : [];

    const id = "sess_" + Date.now();
    const tasks = queries.flatMap(q => configs.map(conf => ({
        term: q, config: conf, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0
    })));

    const settings = { saveSerp: !!saveSerp, useProxies: !!useProxies && lines.length > 0, proxyList: lines };
    if (serpLimit) settings.serpLimit = parseInt(serpLimit, 10) || 100;
    applyProxySettingsToObject(settings, payload);
    settings.behavior = Object.assign({}, DEFAULT_BEHAVIOR, payload.behavior || {});
    if (payload.webhookUrl && /^https?:\/\/\S+$/i.test(payload.webhookUrl.trim())) settings.webhookUrl = payload.webhookUrl.trim();
    if (payload.repeatEveryHours) settings.repeatEveryHours = Math.max(0, parseFloat(payload.repeatEveryHours) || 0);
    if (payload.repeatTimes) settings.repeatTimes = Math.max(0, parseInt(payload.repeatTimes, 10) || 0);
    if (payload.maxCaptchaRounds) settings.maxCaptchaRounds = Math.max(1, parseInt(payload.maxCaptchaRounds, 10) || 10);

    const session = {
        id, name, status: "OPEN", tasks, currentIndex: 0, globalCount: resultsLimit,
        limitType: limitType || "RESULTS",
        delays, settings, originalConfigs: configs, originalQueries: queries,
        baseName: name, runNumber: 1, metrics: ensureMetrics()
    };

    await saveSession(session);
    chrome.runtime.sendMessage({ type: "SESSION_CREATED", payload: { sessionId: id } }).catch(() => { });
    return { sessionId: id, proxy: validateProxyLines(lines) };
}

async function startSession(id) {
    const s = await getSession(id);
    if (!s) return;
    cleanupCaptchaHandling(id);
    if (s.captchaTabId) await closeTab(s.captchaTabId);
    await updateSession(id, x => { x.captchaRounds = 0; x.retryAt = null; x.captchaTabId = null; x.nextRunAt = null; });
    await requestRun(id);
}

async function pauseSession(id) {
    cleanupCaptchaHandling(id);
    const s = await updateSession(id, x => { x.status = "PAUSED"; x.retryAt = null; });
    if (!s) return;
    logToSession(id, "⏸️ PAUSE: Scraper received interrupt signal.");
    broadcastSessionStatus(id);
    if (!runners.has(id)) await releaseProxyIfIdle();
    await startNextQueued();
}

async function deleteSession(id) {
    cleanupCaptchaHandling(id);
    const s0 = await getSession(id);
    if (s0 && s0.captchaTabId) await closeTab(s0.captchaTabId);
    if (!db) await initDB();
    await new Promise((resolve) => {
        const tx = db.transaction([STORE_SESSIONS, STORE_RESULTS, STORE_LOGS], "readwrite");
        tx.objectStore(STORE_SESSIONS).delete(id);
        tx.objectStore(STORE_RESULTS).delete(IDBKeyRange.bound(id + "_", id + "_￿"));
        const logReq = tx.objectStore(STORE_LOGS).openCursor();
        logReq.onsuccess = () => {
            const c = logReq.result;
            if (!c) return;
            if (c.value.sessionId === id) c.delete();
            c.continue();
        };
        tx.oncomplete = resolve;
        tx.onerror = resolve;
    });
    await resetProxyState(id);
    await releaseProxyIfIdle();
    broadcastSessionList();
}

async function finishSession(sessionId) {
    let nextRunAt = null;
    const s = await updateSession(sessionId, x => {
        x.status = "DONE";
        const st = getSettings(x);
        x.nextRunAt = (st.repeatEveryHours > 0 && st.repeatTimes > 0) ? Date.now() + st.repeatEveryHours * 3600000 : null;
        nextRunAt = x.nextRunAt;
    });
    logToSession(sessionId, "🏁 FINISHED: Study completed.");
    if (nextRunAt) logToSession(sessionId, `🔁 Next run scheduled for ${new Date(nextRunAt).toLocaleString()}.`);
    broadcastSessionStatus(sessionId);
    if (s) {
        const m = ensureMetrics(s.metrics);
        await notify(sessionId, "finished", `Finished. Tasks done: ${m.tasksDone}/${s.tasks.length}, failed: ${m.tasksFailed}, captchas: ${m.captchas}.`);
    }
}

async function spawnNextRun(old) {
    await updateSession(old.id, s => { s.nextRunAt = null; });
    const st = getSettings(old);
    if (!(st.repeatEveryHours > 0 && st.repeatTimes > 0)) return;

    const runNo = (old.runNumber || 1) + 1;
    const base = old.baseName || old.name.replace(/ \(run \d+\)$/, "");
    const id = "sess_" + Date.now();
    const settings = JSON.parse(JSON.stringify(old.settings || {}));
    settings.repeatTimes = st.repeatTimes - 1;

    const session = {
        id, name: `${base} (run ${runNo})`, baseName: base, runNumber: runNo, status: "OPEN",
        tasks: old.tasks.filter(t => t.status !== "CANCELLED").map(t => ({ term: t.term, config: t.config, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0 })),
        currentIndex: 0, globalCount: old.globalCount, limitType: old.limitType, delays: old.delays, settings,
        originalConfigs: old.originalConfigs, originalQueries: old.originalQueries, metrics: ensureMetrics()
    };
    await saveSession(session);
    logToSession(id, `🔁 Scheduled repeat of "${old.name}" (run ${runNo}). Starting now.`);
    logToSession(old.id, `🔁 Next run created: "${session.name}".`);
    chrome.runtime.sendMessage({ type: "SESSION_CREATED", payload: { sessionId: id } }).catch(() => { });
    broadcastSessionList();
    await requestRun(id);
}

// --- 10. SCRAPER CORE ---
function pickNextTaskIndex(session, settings) {
    const open = session.tasks.map((t, i) => ({ t, i })).filter(x => x.t.status === "OPEN");
    if (open.length === 0) return -1;
    const partial = open.find(x => x.t.pages.length > 0);
    if (partial) return partial.i;
    if (settings.behavior.shuffle) return open[rndInt(0, open.length - 1)].i;
    return open[0].i;
}

function buildHomeUrl(taskConfig, engineConfig) {
    const typing = engineConfig.typing;
    const u = new URL(typing.homeUrl.replace("{domain}", taskConfig.domain || ""));
    const p = engineConfig.request.params || {};
    if (typing.homeParams !== false) {
        if (p.country && taskConfig.countryCode) u.searchParams.set(p.country, taskConfig.countryCode);
        if (p.language && taskConfig.langCode) u.searchParams.set(p.language, taskConfig.langCode);
    }
    return u.toString();
}

function typedSearchAllowed(settings, task, engineConfig, resumed) {
    if (!settings.behavior.typedSearch || resumed) return false;
    if (!engineConfig.typing || !engineConfig.typing.homeUrl) return false;
    const feat = engineConfig.request && engineConfig.request.features;
    if (feat && feat.requiresUuleEncoding && task.config.location) return false;
    return true;
}

/** Network-level failure (proxy dead, DNS, timeout) as opposed to a scraping problem. */
function isNetworkError(e) { return !!(e && e.message && e.message.startsWith("NETWORK:")); }

async function assertTabLoaded(tabId) {
    const t = await chrome.tabs.get(tabId).catch(() => null);
    if (!t) throw new Error("Tab was closed");
    if ((t.url || "").startsWith("chrome-error://")) throw new Error("NETWORK: browser error page (proxy/connection failed)");
    return t;
}

async function processNextTask(sessionId) {
    const session = await getSession(sessionId);
    if (!session || session.status !== "RUNNING") return "stop";
    const settings = getSettings(session);
    const log = (m, l) => logToSession(sessionId, m, l);

    const idx = pickNextTaskIndex(session, settings);
    if (idx === -1) { await finishSession(sessionId); return "stop"; }

    if (session.activeTabId) { await closeTab(session.activeTabId); }
    await updateSession(sessionId, s => { s.currentIndex = idx; s.activeTabId = null; });

    const task = session.tasks[idx];
    const engineConfig = await getEngine(task.config.engineId);
    if (!engineConfig) {
        log(`❌ ERROR: Plugin for '${task.config.engineId}' not found!`, "ERROR");
        task.status = "FAILED";
        await persistTask(sessionId, idx, task);
        return "continue";
    }

    // --- proxy for this task ---
    const proxyEntries = settings.useProxies ? parseProxyList(settings.proxyList).entries : [];
    if (proxyEntries.length > 0) {
        const cookieDomains = await sessionCookieDomains(session);
        if (await proxyBudgetExceeded(sessionId, settings)) {
            const r = await proxyRotate({ sessionId, settings, reason: "budget", log, cookieDomains });
            if (r.rotated) await updateSession(sessionId, s => { const m = s.metrics = ensureMetrics(s.metrics); m.rotations++; });
            else await proxyEnsureApplied({ sessionId, settings, log, cookieDomains });
        } else {
            const ok = await proxyEnsureApplied({ sessionId, settings, log, cookieDomains });
            if (!ok) {
                const wait = Math.max(5, await proxyMinutesUntilAvailable(sessionId, settings));
                await enterWaitMode(sessionId, null, wait, "All proxies are cooling down.");
                return "stop";
            }
        }
    } else if (await proxyIsActive()) {
        await clearProxyConfig();
    }

    // --- where to start ---
    const firstUrl = buildSearchUrl(task.term, task.config, engineConfig);
    let startUrl = firstUrl;
    let resumed = false;
    if (task.pages.length > 0) {
        if (task.resume && task.resume.page === task.pages.length + 1 && task.resume.url && task.resume.url !== firstUrl) {
            startUrl = task.resume.url;
            resumed = true;
            log(`↪️ RESUME: Continuing "${task.term}" at page ${task.pages.length + 1}.`);
        } else {
            log(`↪️ RESUME: No page link stored. Restarting "${task.term}" from page 1.`, "WARN");
            task.pages = [];
            task.totalOrganic = 0;
        }
    }

    let collectedOrganic = task.totalOrganic || 0;
    let currentPage = task.pages.length + 1;
    const existingUrls = new Set();
    task.pages.forEach(p => p.results.organic.forEach(r => existingUrls.add(r.url)));

    const useTyped = typedSearchAllowed(settings, task, engineConfig, resumed);
    log(`🚀 TASK START: "${task.term}" using ${engineConfig.engine.name}${useTyped ? " (typed search)" : ""}`);
    broadcastSessionStatus(sessionId);

    let tabId = null;
    let outcome = "continue";
    const localeState = { tried: new Set() };
    try {
        const entryUrl = useTyped ? buildHomeUrl(task.config, engineConfig) : startUrl;
        log(`🔗 INITIALIZING: ${entryUrl}`);

        const tab = await new Promise(r => chrome.tabs.create({ url: entryUrl, active: true }, r));
        tabId = tab.id;
        await updateSession(sessionId, s => { s.activeTabId = tabId; });

        if (useTyped) {
            const ok = await typedSearch(tabId, task, engineConfig, settings, log);
            if (!ok) {
                log("⚠️ Typed search did not reach a results page. Falling back to a direct URL.", "WARN");
                await chrome.tabs.update(tabId, { url: firstUrl });
            }
        }

        while (true) {
            const fresh = await getSession(sessionId);
            if (!fresh || fresh.status !== "RUNNING") { outcome = "paused"; break; }
            const limitMode = fresh.limitType || "RESULTS";
            const goal = fresh.globalCount;
            const more = limitMode === "PAGES" ? currentPage <= goal : collectedOrganic < goal;
            if (!more || currentPage > MAX_PAGES) break;

            log(`🌐 LOADING: Waiting for Page ${currentPage}...`);
            await waitForTabSmart(tabId);
            let loaded = await assertTabLoaded(tabId);
            if (await isPaused(sessionId)) { outcome = "paused"; break; }
            if (await enforceLocale(tabId, task, engineConfig, log, localeState)) loaded = await assertTabLoaded(tabId);

            try {
                await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
            } catch (e) {
                await assertTabLoaded(tabId);
                throw e;
            }
            await sleep(pacedDelay(1800, 4200, settings.behavior.humanPacing));

            const preCheck = await sendToTab(tabId, { action: "CHECK_CAPTCHA", payload: { config: engineConfig } }, 15000);
            if (preCheck && preCheck.isCaptcha) {
                await persistTask(sessionId, idx, task);
                outcome = (await handleCaptchaEvent(sessionId, tabId, { idx })) === "rotated" ? "fast" : "stop";
                return outcome;
            }

            log(`📜 BEHAVIOR: Executing human logic (Page ${currentPage})...`);
            await preparePage(tabId, engineConfig, settings, log);
            await sleep(pacedDelay(2000, 5000, settings.behavior.humanPacing));
            if (await isPaused(sessionId)) { outcome = "paused"; break; }

            const serpLimit = settings.serpLimit || 100;
            const shouldSaveSerp = (settings.saveSerp || settings.saveScreenshots || settings.saveHtml) && (task.pages.length < serpLimit);

            let screenshotData = null;
            if (shouldSaveSerp) {
                if (engineConfig.request && engineConfig.request.features && engineConfig.request.features.disableScreenshots) {
                    log(`⚠️ SKIPPING SCREENSHOT: ${engineConfig.engine.name} is incompatible with full-page captures due to Chrome memory limits.`, "WARN");
                } else {
                    log("📸 CAPTURING: Full page screenshot...");
                    try { screenshotData = await captureFullPage(tabId, engineConfig); }
                    catch (e) { log(`⚠️ SCREENSHOT FAILED: ${e && e.message || e}`); }
                }
            }
            if (await isPaused(sessionId)) { outcome = "paused"; break; }

            log("🔍 SCRAPING: Extracting data using plugin rules...");
            const response = await sendToTab(tabId, { action: "SCRAPE_SERP", payload: { startRank: collectedOrganic, config: engineConfig } }, 90000);

            if (response && response.isCaptcha) {
                await persistTask(sessionId, idx, task);
                outcome = (await handleCaptchaEvent(sessionId, tabId, { idx })) === "rotated" ? "fast" : "stop";
                return outcome;
            }
            if (!response || !response.data) throw new Error("Scrape failed (Content Script did not return data).");

            const data = response.data;
            const newOrganic = (data.organic || []).filter(r => !existingUrls.has(r.url));
            const newImages = (data.images || []).filter(r => !existingUrls.has(r.url));
            const newVideos = (data.videos || []).filter(r => !existingUrls.has(r.url));
            newOrganic.forEach(r => existingUrls.add(r.url));
            newImages.forEach(r => existingUrls.add(r.url));
            newVideos.forEach(r => existingUrls.add(r.url));

            let finalOrganicForPage = newOrganic, finalImagesForPage = newImages, finalVideosForPage = newVideos;
            if (limitMode === "RESULTS") {
                const remainingQuota = goal - collectedOrganic;
                finalOrganicForPage = newOrganic.slice(0, Math.max(0, remainingQuota));
                finalImagesForPage = newImages.slice(0, Math.max(0, remainingQuota - finalOrganicForPage.length));
                finalVideosForPage = newVideos.slice(0, Math.max(0, remainingQuota - finalOrganicForPage.length - finalImagesForPage.length));
            }
            data.organic = finalOrganicForPage;
            data.images = finalImagesForPage;
            data.videos = finalVideosForPage;

            const aiFound = (data.ai_overview && data.ai_overview.found) ? "YES" : "NO";
            const aiSegs = (data.ai_overview && data.ai_overview.segments) ? data.ai_overview.segments.length : 0;
            const adsCount = data.ads ? data.ads.length : 0;
            const totalNew = finalOrganicForPage.length + finalImagesForPage.length + finalVideosForPage.length;

            log(`📊 P${currentPage}: AI: ${aiFound} (${aiSegs} Segs) | Ads: ${adsCount} | Img: ${finalImagesForPage.length} | Vid: ${finalVideosForPage.length} | Org: ${finalOrganicForPage.length} | New: ${totalNew}`);

            await savePageContent(sessionId, idx, currentPage, { html: shouldSaveSerp ? response.html_content : null, screenshot: screenshotData });
            task.pages.push({ pageNumber: currentPage, results: data });
            collectedOrganic += totalNew;
            task.totalOrganic = collectedOrganic;
            task.resume = null;
            await persistTask(sessionId, idx, task);

            const stats = await recordPageMetrics(sessionId, task, currentPage, totalNew, aiFound === "YES", adsCount);
            if (proxyEntries.length > 0) await proxyCountRequest(sessionId, settings);
            if (stats.zeroStreak >= 3) {
                await pauseForAttention(sessionId, `${stats.zeroStreak} searches in a row returned no results. The page layout may have changed (selectors broken) or the IP is being served empty pages. Check the engine and the SERP manually.`);
                outcome = "stop";
                return outcome;
            }

            if (limitMode === "RESULTS" && collectedOrganic >= goal) { log(`✅ TARGET MET: Collected ${collectedOrganic} results.`); break; }
            if (limitMode === "PAGES" && currentPage >= goal) { log(`✅ TARGET MET: Scraped ${goal} pages.`); break; }
            if (await isPaused(sessionId)) { outcome = "paused"; break; }

            const nav = await goToNextPage(tabId, engineConfig, settings, task, idx, currentPage, sessionId);
            if (nav && nav.isCaptcha) {
                await persistTask(sessionId, idx, task);
                outcome = (await handleCaptchaEvent(sessionId, tabId, { idx })) === "rotated" ? "fast" : "stop";
                return outcome;
            }
            if (!nav || !nav.success) { log("⏹️ END: No more search pages or selector failed."); break; }

            currentPage++;
            const cur = await getSession(sessionId);
            const d = (cur && cur.delays) || session.delays;
            const wait = pacedDelay(d.min, d.max, settings.behavior.humanPacing);
            log(`😴 IDLE: Random wait ${Math.round(wait / 1000)}s...`);
            if (!(await sleepWhileRunning(sessionId, wait))) { outcome = "paused"; break; }
        }

        const finalCheck = await getSession(sessionId);
        if (outcome === "continue" && finalCheck && finalCheck.status === "RUNNING") {
            task.status = "DONE";
            task.resume = null;
            await persistTask(sessionId, idx, task);
            await updateSession(sessionId, s => {
                const m = s.metrics = ensureMetrics(s.metrics);
                m.tasksDone++; m.tasksSinceBreak++; m.failStreak = 0;
            });
            log(`✔️ TASK COMPLETED: "${task.term}"`);
        } else if (outcome === "paused") {
            await persistTask(sessionId, idx, task);
            outcome = "stop";
        }
    } catch (error) {
        log(`❌ ERROR: ${error.message}`, "ERROR");
        outcome = (await handleTaskError(sessionId, idx, task, error, settings, log)) || "continue";
    } finally {
        const check = await getSession(sessionId);
        if (tabId && (!check || check.status !== "PAUSED_CAPTCHA")) await closeTab(tabId);
        if (check && check.activeTabId === tabId) await updateSession(sessionId, s => { s.activeTabId = null; });
    }
    return outcome;
}

async function handleTaskError(sessionId, idx, task, error, settings, log) {
    if (await isPaused(sessionId)) { await persistTask(sessionId, idx, task); return "stop"; }

    const network = isNetworkError(error);
    task.retryCount = (task.retryCount || 0) + 1;
    const maxRetries = network && settings.useProxies ? 6 : 3;
    let status = "continue";

    if (network && settings.useProxies && parseProxyList(settings.proxyList).entries.length > 0) {
        const s = await getSession(sessionId);
        const r = await proxyRotate({ sessionId, settings, reason: "network_error", log, cookieDomains: s ? await sessionCookieDomains(s) : [] });
        if (r.rotated) await updateSession(sessionId, x => { const m = x.metrics = ensureMetrics(x.metrics); m.rotations++; });
        else if (r.exhausted) {
            await persistTask(sessionId, idx, task);
            await enterWaitMode(sessionId, null, 15, "All proxies failed or are cooling down.");
            return "stop";
        }
    }

    if (task.retryCount > maxRetries) {
        task.status = "FAILED";
        log(`💀 FAILED: Abandoning after ${maxRetries} retries. Error: ${error.message}`, "ERROR");
        let streak = 0;
        await updateSession(sessionId, s => { const m = s.metrics = ensureMetrics(s.metrics); m.tasksFailed++; m.failStreak++; streak = m.failStreak; });
        await persistTask(sessionId, idx, task);
        if (streak >= 5) {
            await pauseForAttention(sessionId, `${streak} tasks failed in a row. Last error: ${error.message}`);
            return "stop";
        }
    } else {
        log(`⚠️ RETRY ${task.retryCount}/${maxRetries} shortly... Reason: ${error.message}`, "WARN");
        task.status = "OPEN";
        await persistTask(sessionId, idx, task);
        if (!(await sleepWhileRunning(sessionId, 5000 * task.retryCount))) status = "stop";
    }
    return status;
}

async function recordPageMetrics(sessionId, task, pageNum, total, hasAi, adsCount) {
    let result = null;
    await updateSession(sessionId, s => {
        const m = s.metrics = ensureMetrics(s.metrics);
        const key = variantKey(task.config);
        const v = m.byVariant[key] || (m.byVariant[key] = { pages: 0, results: 0, zeroPages: 0, captchas: 0, ai: 0, ads: 0 });
        m.pages++; m.results += total;
        v.pages++; v.results += total; v.ai += hasAi ? 1 : 0; v.ads += adsCount;
        if (total === 0) { m.zeroPages++; v.zeroPages++; }
        if (pageNum === 1) m.zeroStreak = total === 0 ? m.zeroStreak + 1 : 0;
        s.captchaRounds = 0;
        result = { zeroStreak: m.zeroStreak };
    });
    return result || { zeroStreak: 0 };
}

// --- 11. BROWSER INTERACTION ---
function sendToTab(tabId, msg, ms = 60000) {
    return Promise.race([
        chrome.tabs.sendMessage(tabId, msg).catch(() => null),
        new Promise(r => setTimeout(() => r(null), ms))
    ]);
}

function waitForTabSmart(tabId, timeoutMs = 60000) {
    return new Promise((resolve, reject) => {
        let done = false;
        const finish = (err) => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            chrome.tabs.onUpdated.removeListener(l);
            err ? reject(err) : resolve();
        };
        const l = (id, chg) => { if (id === tabId && chg.status === "complete") finish(); };
        const timer = setTimeout(() => finish(new Error("NETWORK: page load timeout")), timeoutMs);
        chrome.tabs.onUpdated.addListener(l);
        chrome.tabs.get(tabId, (t) => {
            if (chrome.runtime.lastError || !t) return finish(new Error("Tab was closed"));
            if (t.status === "complete") finish();
        });
    });
}

async function waitForUrlChange(tabId, beforeUrl, timeoutMs) {
    const t0 = Date.now();
    while (Date.now() - t0 < timeoutMs) {
        const t = await chrome.tabs.get(tabId).catch(() => null);
        if (!t) return false;
        if (t.url && t.url !== beforeUrl && t.status === "complete") return true;
        await sleep(250);
    }
    return false;
}

function getParamCI(u, key) {
    const k = key.toLowerCase();
    for (const [name, v] of u.searchParams) if (name.toLowerCase() === k) return v;
    return null;
}

/**
 * Makes sure the open results page carries the configured country/language parameters. Typed search, redirects
 * and the engines' own next-page links can drop them. Corrects the URL at most once per parameter and task.
 */
const localeDropped = new Set();

async function enforceLocale(tabId, task, engineConfig, log, state) {
    const p = (engineConfig.request && engineConfig.request.params) || {};
    const t = await chrome.tabs.get(tabId).catch(() => null);
    if (!t || !t.url) return false;
    let u, base;
    try {
        u = new URL(t.url);
        base = new URL(engineConfig.request.baseUrl.replace("{domain}", task.config.domain || ""));
    } catch (e) { return false; }
    if (u.host !== base.host || u.pathname !== base.pathname) return false;
    const want = [];
    if (p.country && task.config.countryCode) want.push([p.country, task.config.countryCode]);
    if (p.language && task.config.langCode) want.push([p.language, task.config.langCode]);
    const changed = [];
    for (const [key, val] of want) {
        if (state.tried.has(key) || localeDropped.has(base.host + "|" + key)) continue;
        const cur = getParamCI(u, key);
        if (cur !== null && cur.toLowerCase() === val.toLowerCase()) continue;
        for (const name of Array.from(u.searchParams.keys())) if (name.toLowerCase() === key.toLowerCase()) u.searchParams.delete(name);
        u.searchParams.set(key, val);
        state.tried.add(key);
        changed.push(key);
        log(`🌍 Parameter "${key}" was ${cur === null ? "missing" : "\"" + cur + "\""} on the results page. Reloading with "${key}=${val}".`, "WARN");
    }
    if (!changed.length) return false;
    await chrome.tabs.update(tabId, { url: u.toString() });
    await sleep(800);
    await waitForTabSmart(tabId);
    const after = await chrome.tabs.get(tabId).catch(() => null);
    try {
        const au = new URL(after.url);
        for (const key of changed) {
            if (au.host === base.host && getParamCI(au, key) === null) {
                localeDropped.add(base.host + "|" + key);
                log(`🌍 ${base.host} removes "${key}" itself. Not correcting it again.`, "WARN");
            }
        }
    } catch (e) { }
    return true;
}

async function typedSearch(tabId, task, engineConfig, settings, log) {
    const typing = engineConfig.typing;
    try {
        await waitForTabSmart(tabId);
        await assertTabLoaded(tabId);
        await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
        await sleep(pacedDelay(1200, 3200, true));

        await withCdp(tabId, async () => {
            await dismissOverlays(tabId, engineConfig);
        }).catch(() => { });

        const selectors = typing.inputSelectors || [typing.inputSelector];
        const found = await sendToTab(tabId, { action: "GET_ELEMENT_RECT", payload: { selectors } }, 10000);
        if (!found || !found.found) { log("⚠️ Typed search: search box not found.", "WARN"); return false; }

        const before = (await chrome.tabs.get(tabId)).url;
        log("⌨️ Typed search: search box found, typing query...", "INFO");
        await withCdp(tabId, async () => {
            await cdpWander(tabId, null);
            await cdpClickRect(tabId, found.rect);
            await sleep(rndInt(250, 700));
            await cdpTypeText(tabId, task.term, { typoChance: settings.behavior.humanPacing ? 0.025 : 0 });
            await sleep(lognormalMs(650, 0.4, 300, 1800));
            await cdpPressSpecial(tabId, "Enter");
        });

        const ok = await waitForUrlChange(tabId, before, 25000);
        if (!ok) {
            const now = await chrome.tabs.get(tabId).catch(() => null);
            log(`⚠️ Typed search: no results page after pressing Enter (tab: ${now ? now.status + ", " + String(now.url).slice(0, 80) : "gone"}).`, "WARN");
            return false;
        }

        await sleep(1500);
        const after = (await chrome.tabs.get(tabId)).url || "";
        const p = engineConfig.request.params || {};
        const missing = [];
        try {
            const u = new URL(after);
            if (p.country && task.config.countryCode && !u.searchParams.has(p.country)) missing.push(p.country);
            if (p.language && task.config.langCode && !u.searchParams.has(p.language)) missing.push(p.language);
        } catch (e) { }
        if (missing.length) log(`⚠️ Typed search: results URL has no "${missing.join(", ")}" parameter. Results may not be localised as configured.`, "WARN");
        return true;
    } catch (e) {
        log(`⚠️ Typed search failed: ${e.message}`, "WARN");
        return false;
    }
}

/** Clicks the element returned by the last GET_CLICK_TARGET, but only if it is still uncovered and not a link. */
async function clickVerifiedTarget(tabId, log, label) {
    let v = null;
    for (let attempt = 0; attempt < 3; attempt++) {
        v = await sendToTab(tabId, { action: "VERIFY_TARGET" }, 5000);
        if ((v && v.ok) || (v && v.reason === "link")) break;
        await sleep(rndInt(500, 900));
    }
    if (!v || !v.ok) {
        if (log) log(`🖱️ ${label || "Click target"} skipped: ${v ? v.reason : "no answer from page"}`, "INFO");
        return false;
    }
    await cdpClickRect(tabId, v.rect);
    return true;
}

/** Same results page (host, path, tab type)? A different one means a click opened Images, Shopping etc. */
function sameSerp(a, b) {
    try {
        const x = new URL(a), y = new URL(b);
        return x.host === y.host && x.pathname === y.pathname && ["tbm", "udm"].every(k => x.searchParams.get(k) === y.searchParams.get(k));
    } catch (e) { return true; }
}

/** If a click navigated away from the results page, load the page again. Returns true when that happened. */
async function recoverIfLeft(tabId, expectedUrl, log) {
    const t = await chrome.tabs.get(tabId).catch(() => null);
    if (!t) return false;
    const now = t.pendingUrl || t.url || "";
    if (!now || sameSerp(now, expectedUrl)) return false;
    log(`⚠️ A click left the results page (now: ${now.slice(0, 90)}). Loading the results again.`, "WARN");
    await chrome.tabs.update(tabId, { url: expectedUrl });
    await sleep(800);
    await waitForTabSmart(tabId);
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
    return true;
}

async function dismissOverlays(tabId, engineConfig, guard, log) {
    for (const kind of ["consent", "popup"]) {
        for (let i = 0; i < 3; i++) {
            const t = await sendToTab(tabId, { action: "GET_CLICK_TARGET", payload: { config: engineConfig, kind } }, 10000);
            if (!t || !t.found) break;
            if (!(await clickVerifiedTarget(tabId, log, kind + " target"))) continue;
            if (log) log(`🖱️ ${kind} click`, "INFO");
            await sleep(rndInt(900, 1700));
            if (kind === "popup" && guard && await guard()) return;
        }
    }
}

async function trustedScroll(tabId) {
    for (let step = 0; step < 14; step++) {
        const m = await sendToTab(tabId, { action: "GET_METRICS" }, 5000);
        if (!m || m.scrollY + m.innerHeight >= m.scrollHeight - 40) break;
        await cdpWheelScroll(tabId, rndInt(280, 650), 1);
        await sleep(lognormalMs(450, 0.5, 150, 1800));
    }
    await sleep(rndInt(600, 1400));
    for (let i = 0; i < 10; i++) {
        const m = await sendToTab(tabId, { action: "GET_METRICS" }, 5000);
        if (!m || m.scrollY < 30) break;
        await cdpWheelScroll(tabId, Math.min(Math.ceil(m.scrollY), rndInt(500, 900)), -1);
        await sleep(rndInt(100, 300));
    }
}

async function trustedExpand(tabId, engineConfig, guard, log) {
    if (!engineConfig.behavior || !engineConfig.behavior.aiExpandSelectors) return;
    for (let i = 0; i < 6; i++) {
        const t = await sendToTab(tabId, { action: "GET_CLICK_TARGET", payload: { config: engineConfig, kind: "expand" } }, 10000);
        if (!t || !t.found) break;
        const ok = await clickVerifiedTarget(tabId, log, "Expand target");
        if (log) log(ok ? `🖱️ Expand click: "${t.label || ''}"` : `🖱️ Expand target "${t.label || ''}" skipped (covered or moved)`, "INFO");
        if (!ok) continue;
        await sleep(rndInt(1200, 2200));
        if (guard && await guard()) break;
    }
}

/** Cookie banners, scrolling and AI-overview expansion. Uses real (trusted) input events when possible. */
async function preparePage(tabId, engineConfig, settings, log) {
    const infinite = engineConfig.selectors && engineConfig.selectors.pagination && engineConfig.selectors.pagination.type === "infinite_scroll";
    if (!settings.behavior.trustedInput) {
        await sendToTab(tabId, { action: "SCROLL_AND_PREPARE", payload: { config: engineConfig } });
        return;
    }
    try {
        const startUrl = ((await chrome.tabs.get(tabId)).url) || "";
        let left = false;
        const guard = async () => { if (left) return true; left = await recoverIfLeft(tabId, startUrl, log); return left; };
        log("🖱️ Step: attaching trusted input.", "INFO");
        setCdpBudget(180000);
        await withCdp(tabId, async () => {
            log("🖱️ Step: overlays.", "INFO");
            await dismissOverlays(tabId, engineConfig, guard, log);
            const vp = await sendToTab(tabId, { action: "GET_METRICS" }, 5000);
            log("🖱️ Step: mouse movement.", "INFO");
            await cdpWander(tabId, vp ? { w: vp.innerWidth, h: vp.innerHeight } : null);
            log("🖱️ Step: scrolling.", "INFO");
            if (!infinite) await trustedScroll(tabId);
            log("🖱️ Step: expand.", "INFO");
            if (!left) await trustedExpand(tabId, engineConfig, guard, log);
        });
        setCdpBudget(0);
        log("🖱️ Step: done.", "INFO");
        if (infinite) await sendToTab(tabId, { action: "SCROLL_AND_PREPARE", payload: { config: engineConfig, skipInteractions: true } });
    } catch (e) {
        setCdpBudget(0);
        log(`⚠️ Trusted input unavailable (${e.message}). Falling back to scripted behaviour.`, "WARN");
        await sendToTab(tabId, { action: "SCROLL_AND_PREPARE", payload: { config: engineConfig } });
    }
}

async function goToNextPage(tabId, engineConfig, settings, task, idx, currentPage, sessionId) {
    const infinite = engineConfig.selectors.pagination && engineConfig.selectors.pagination.type === "infinite_scroll";
    if (settings.behavior.trustedInput && !infinite) {
        const r = await sendToTab(tabId, { action: "GET_NEXT_RECT", payload: { config: engineConfig } }, 15000);
        if (r && r.isCaptcha) return { isCaptcha: true };
        if (r && r.found === false) return { success: false };
        if (r && r.found && r.rect) {
            task.resume = r.href ? { page: currentPage + 1, url: r.href } : null;
            await persistTask(sessionId, idx, task);
            try {
                const before = (await chrome.tabs.get(tabId)).url;
                await withCdp(tabId, () => cdpClickRect(tabId, r.rect));
                if (r.href) await waitForUrlChange(tabId, before, 25000);
                else await sleep(1500);
                return { success: true };
            } catch (e) {
                logToSession(sessionId, `⚠️ Trusted click failed (${e.message}). Using scripted click.`, "WARN");
            }
        }
    }
    const nav = await sendToTab(tabId, { action: "NAVIGATE_NEXT", payload: { config: engineConfig } }, 30000);
    return nav;
}

// --- 12. UTILITIES ---
function buildSearchUrl(term, taskConfig, engineConfig) {
    const reqData = engineConfig.request;

    let u = reqData.baseUrl.replace("{domain}", taskConfig.domain || "");
    const urlObj = new URL(u);

    if (reqData.params.query) urlObj.searchParams.set(reqData.params.query, term);
    if (reqData.params.country && taskConfig.countryCode) urlObj.searchParams.set(reqData.params.country, taskConfig.countryCode);
    if (reqData.params.language && taskConfig.langCode) urlObj.searchParams.set(reqData.params.language, taskConfig.langCode);

    let uuleValue = null;
    if (reqData.features && reqData.features.requiresUuleEncoding && taskConfig.location) {
        if (taskConfig.location.startsWith("w+CAIQICI")) uuleValue = taskConfig.location;
        else uuleValue = generateUule(taskConfig.location);
    }

    let finalUrl = urlObj.toString();
    if (uuleValue) finalUrl += (finalUrl.includes('?') ? '&' : '?') + reqData.params.location + '=' + uuleValue;
    return finalUrl;
}

function generateUule(loc) {
    const secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    return `w+CAIQICI${secret[loc.length % 65]}${btoa(loc)}`;
}

async function captureFullPage(tabId, engineConfig) {
    await sendToTab(tabId, { action: "GET_DIMENSIONS", payload: { config: engineConfig } }, 10000);
    await sleep(500);
    return withCdp(tabId, async () => {
        const res = await cdpSend(tabId, "Page.captureScreenshot", { format: "jpeg", quality: 100, fromSurface: true, captureBeyondViewport: true });
        if (!res || !res.data) throw new Error("No image data received");
        return "data:image/jpeg;base64," + res.data;
    });
}

// --- 13. BROADCASTS ---
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

const statusTimers = new Map();
function broadcastSessionStatus(id, immediate = false) {
    if (immediate) { doBroadcastSessionStatus(id); return; }
    if (statusTimers.has(id)) return;
    statusTimers.set(id, setTimeout(() => { statusTimers.delete(id); doBroadcastSessionStatus(id); }, 200));
}

async function doBroadcastSessionStatus(id) {
    const s = await getSession(id);
    if (!s) return;
    const logs = await getLogs(id);
    const current = s.tasks[s.currentIndex];
    const settings = getSettings(s);

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
            settings,
            globalCount: s.globalCount,
            limitType: s.limitType || "RESULTS",
            metrics: ensureMetrics(s.metrics),
            proxy: settings.useProxies ? await proxyOverview(id, settings) : null,
            retryAt: s.retryAt || null,
            nextRunAt: s.nextRunAt || null,
            runNumber: s.runNumber || 1
        }
    }).catch(() => { });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function updateSessionDelay(payload) {
    const s = await updateSession(payload.sessionId, x => { x.delays = { min: payload.min * 1000, max: payload.max * 1000 }; });
    if (s) {
        logToSession(payload.sessionId, `⏱️ Delay updated to ${payload.min}-${payload.max}s`);
        broadcastSessionStatus(payload.sessionId);
    }
}

async function updateSessionLimit(payload) {
    const s = await updateSession(payload.sessionId, x => {
        x.globalCount = parseInt(payload.limit);
        if (payload.limitType) x.limitType = payload.limitType;
    });
    if (s) {
        logToSession(payload.sessionId, `🎯 Limit updated to ${s.globalCount} ${s.limitType === 'PAGES' ? 'Pages' : 'Results'}`);
        broadcastSessionStatus(payload.sessionId);
    }
}

async function updateSessionStorageSettings(payload) {
    const { sessionId, saveSerp, serpLimit } = payload;
    const s = await updateSession(sessionId, session => {
        if (!session.settings) session.settings = {};
        session.settings.saveSerp = !!saveSerp;
        if (serpLimit !== undefined) session.settings.serpLimit = serpLimit;
        session.settings.saveScreenshots = false;
        session.settings.saveHtml = false;
    });
    if (s) {
        logToSession(sessionId, `💾 Storage Settings updated. Save SERP: ${!!saveSerp}, Limit: ${s.settings.serpLimit}`);
        broadcastSessionStatus(sessionId);
    }
}

// --- 14. BOOT: runs every time the service worker starts ---
(async () => {
    try {
        await initDB();
        ensureWatchdogAlarm();
        await watchdog();
    } catch (e) { console.error("boot failed", e); }
})();
