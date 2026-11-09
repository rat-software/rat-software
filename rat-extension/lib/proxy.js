/**
 * @file lib/proxy.js
 * Provider-agnostic proxy handling: parsing, rotation (list / gateway), health checks,
 * persistent proxy auth (survives service-worker restarts) and per-IP cooldowns.
 * Loaded into the service worker via importScripts().
 */

const DEFAULT_IP_ECHO_URLS = ["https://ipinfo.io/json", "https://api.ipify.org?format=json"];
const PROXY_AUTH_KEY = "rat_proxy_auth";
const PROXY_ACTIVE_KEY = "rat_proxy_active";

let proxyAuthCache = null;

function randomToken(len = 8) {
    const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    let out = "";
    for (let i = 0; i < len; i++) out += chars[Math.floor(Math.random() * chars.length)];
    return out;
}

// --- PARSING ---------------------------------------------------------------

/**
 * Accepts: host:port | host:port:user:pass | user:pass@host:port | scheme://[user:pass@]host:port
 * Returns null for empty/comment lines, {error} for unusable lines, otherwise an entry.
 */
function parseProxyLine(line) {
    line = (line || "").trim();
    if (!line || line.startsWith("#")) return null;

    let scheme = "http";
    let rest = line;
    const m = rest.match(/^([a-z0-9]+):\/\/(.*)$/i);
    if (m) { scheme = m[1].toLowerCase(); rest = m[2].replace(/\/+$/, ""); }
    if (!["http", "https", "socks4", "socks5"].includes(scheme)) return { raw: line, error: `Unsupported scheme "${scheme}"` };

    let host = "", port = "", user = "", pass = "";
    const safeDecode = (s) => { try { return decodeURIComponent(s); } catch (e) { return s; } };

    if (rest.includes("@")) {
        const at = rest.lastIndexOf("@");
        const cred = rest.slice(0, at);
        const hostPort = rest.slice(at + 1);
        const ci = cred.indexOf(":");
        user = safeDecode(ci >= 0 ? cred.slice(0, ci) : cred);
        pass = safeDecode(ci >= 0 ? cred.slice(ci + 1) : "");
        const hp = hostPort.split(":");
        if (hp.length !== 2) return { raw: line, error: "Expected host:port after '@'" };
        [host, port] = hp;
    } else {
        const parts = rest.split(":");
        if (parts.length === 2) {
            [host, port] = parts;
        } else if (parts.length >= 4) {
            host = parts[0]; port = parts[1]; user = parts[2]; pass = parts.slice(3).join(":");
        } else {
            return { raw: line, error: "Unrecognised format (use host:port:user:pass)" };
        }
    }

    const portNum = parseInt(port, 10);
    if (!host || !(portNum > 0 && portNum < 65536)) return { raw: line, error: "Invalid host or port" };
    if (scheme.startsWith("socks") && user) return { raw: line, error: "Chrome does not support SOCKS proxies with username/password. Use the provider's HTTP endpoint." };

    return { scheme, host, port: portNum, user, pass, raw: line, key: `${host}:${portNum}:${user}` };
}

function parseProxyList(lines) {
    const entries = [];
    const errors = [];
    (lines || []).forEach((l) => {
        const p = parseProxyLine(l);
        if (!p) return;
        if (p.error) errors.push(p); else entries.push(p);
    });
    return { entries, errors };
}

function maskProxyForLog(entry) {
    return `${entry.host}:${entry.port}`;
}

// --- STATE -----------------------------------------------------------------

function proxyStateKey(sessionId) { return `proxy_state_${sessionId}`; }

async function getProxyState(sessionId) {
    const k = proxyStateKey(sessionId);
    const data = await chrome.storage.local.get(k);
    return data[k] || { idx: -1, token: randomToken(), requests: 0, entries: {} };
}

async function saveProxyState(sessionId, state) {
    await chrome.storage.local.set({ [proxyStateKey(sessionId)]: state });
}

async function resetProxyState(sessionId) {
    await chrome.storage.local.remove(proxyStateKey(sessionId));
}

function effectiveProxyUsername(entry, settings, state) {
    const tpl = (settings.proxyMode === "gateway" && settings.proxyUsernameTemplate) ? settings.proxyUsernameTemplate : "";
    if (!tpl) return entry.user;
    return tpl
        .replace(/\{user\}/g, entry.user)
        .replace(/\{session\}/g, state.token || randomToken())
        .replace(/\{rand\}/g, randomToken(6));
}

// --- CHROME PROXY SETTINGS + AUTH -----------------------------------------

function webhookHost(settings) {
    try { return settings.webhookUrl ? new URL(settings.webhookUrl).hostname : null; } catch (e) { return null; }
}

async function applyProxyConfig(entry, username, extraBypass = []) {
    const config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: { scheme: entry.scheme, host: entry.host, port: entry.port },
            bypassList: ["localhost", "127.0.0.1", "<local>", ...extraBypass.filter(Boolean)]
        }
    };
    const auth = entry.user || entry.pass ? { username, password: entry.pass, host: entry.host } : null;
    proxyAuthCache = auth;
    await chrome.storage.local.set({ [PROXY_AUTH_KEY]: auth, [PROXY_ACTIVE_KEY]: true });
    await new Promise((resolve) => chrome.proxy.settings.set({ value: config, scope: "regular" }, resolve));
}

async function clearProxyConfig() {
    proxyAuthCache = null;
    await chrome.storage.local.remove([PROXY_AUTH_KEY, PROXY_ACTIVE_KEY]);
    await new Promise((resolve) => chrome.proxy.settings.clear({ scope: "regular" }, resolve));
}

/** True while this extension has a proxy configured in the browser (it is global for the whole profile). */
async function proxyIsActive() {
    const d = await chrome.storage.local.get(PROXY_ACTIVE_KEY);
    return !!d[PROXY_ACTIVE_KEY];
}

async function loadProxyAuth() {
    if (proxyAuthCache) return proxyAuthCache;
    const data = await chrome.storage.local.get(PROXY_AUTH_KEY);
    proxyAuthCache = data[PROXY_AUTH_KEY] || null;
    return proxyAuthCache;
}

// Only ever answers proxy challenges from the configured proxy host. Website auth prompts get nothing.
const proxyAuthAttempts = new Map();
chrome.webRequest.onAuthRequired.addListener(
    (details, callback) => {
        if (!details.isProxy) { callback({}); return; }
        const n = (proxyAuthAttempts.get(details.requestId) || 0) + 1;
        proxyAuthAttempts.set(details.requestId, n);
        if (proxyAuthAttempts.size > 500) proxyAuthAttempts.clear();

        loadProxyAuth().then((auth) => {
            const challenger = (details.challenger && details.challenger.host || "").toLowerCase();
            if (!auth || n > 2 || (auth.host && challenger && challenger !== auth.host.toLowerCase())) {
                callback({ cancel: true });
            } else {
                callback({ authCredentials: { username: auth.username, password: auth.password } });
            }
        }).catch(() => callback({ cancel: true }));
    },
    { urls: ["<all_urls>"] },
    ["asyncBlocking"]
);

// --- COOKIES ---------------------------------------------------------------

async function clearCookiesForDomains(domains) {
    let removed = 0;
    for (const d of new Set((domains || []).filter(Boolean))) {
        let cookies = [];
        try { cookies = await chrome.cookies.getAll({ domain: d }); } catch (e) { continue; }
        for (const c of cookies) {
            const url = (c.secure ? "https://" : "http://") + c.domain.replace(/^\./, "") + c.path;
            try { await chrome.cookies.remove({ url, name: c.name, storeId: c.storeId }); removed++; } catch (e) {}
        }
    }
    return removed;
}

// --- ROTATION --------------------------------------------------------------

function isCooling(entryState, now) {
    return entryState && entryState.cooldownUntil && entryState.cooldownUntil > now;
}

/**
 * reason: "init" | "captcha" | "network_error" | "budget" | "retry"
 * Returns { rotated, exhausted, entry }.
 */
async function proxyRotate({ sessionId, settings, reason, log, cookieDomains }) {
    const { entries } = parseProxyList(settings.proxyList || []);
    if (entries.length === 0) return { rotated: false, exhausted: false };

    const state = await getProxyState(sessionId);
    const now = Date.now();
    const cooldownMs = Math.max(1, settings.proxyCooldownMin || 120) * 60000;

    const cur = state.idx >= 0 && state.idx < entries.length ? entries[state.idx] : null;
    if (cur) {
        const es = state.entries[cur.key] || (state.entries[cur.key] = { requests: 0, captchas: 0, fails: 0 });
        if (reason === "captcha") { es.captchas++; es.cooldownUntil = now + cooldownMs; }
        if (reason === "network_error") {
            es.fails++;
            es.cooldownUntil = now + (es.fails >= 3 ? 60 : 10) * 60000;
        }
    }

    const gateway = settings.proxyMode === "gateway";
    const candidates = entries
        .map((e, i) => ({ e, i, es: state.entries[e.key] || {} }))
        .filter(({ es }) => gateway || !isCooling(es, now));

    if (candidates.length === 0) {
        await saveProxyState(sessionId, state);
        return { rotated: false, exhausted: true };
    }

    let pool = candidates;
    if (candidates.length > 1) pool = candidates.filter(({ i }) => i !== state.idx);
    pool.sort((a, b) => (a.es.lastUsedAt || 0) - (b.es.lastUsedAt || 0));
    const chosen = pool[0];

    state.idx = chosen.i;
    state.token = randomToken();
    state.requests = 0;
    const es = state.entries[chosen.e.key] || (state.entries[chosen.e.key] = { requests: 0, captchas: 0, fails: 0 });
    es.lastUsedAt = now;
    await saveProxyState(sessionId, state);

    await applyProxyConfig(chosen.e, effectiveProxyUsername(chosen.e, settings, state), [webhookHost(settings)]);

    let cleared = 0;
    if (reason !== "init" && settings.clearCookiesOnRotate !== false) {
        cleared = await clearCookiesForDomains(cookieDomains);
    }
    if (log) log(`🛡️ Proxy → ${maskProxyForLog(chosen.e)}${gateway ? ` (new session ${state.token})` : ""} [${reason}]${cleared ? `, ${cleared} cookies cleared` : ""}`);
    return { rotated: true, exhausted: false, entry: chosen.e };
}

/** Re-applies the current proxy (after a service-worker restart / test run) or picks the first one. */
async function proxyEnsureApplied({ sessionId, settings, log, cookieDomains }) {
    const { entries } = parseProxyList(settings.proxyList || []);
    if (entries.length === 0) return false;
    const state = await getProxyState(sessionId);
    if (state.idx >= 0 && state.idx < entries.length) {
        const e = entries[state.idx];
        const es = state.entries[e.key];
        if (settings.proxyMode !== "gateway" && isCooling(es, Date.now())) {
            const r = await proxyRotate({ sessionId, settings, reason: "retry", log, cookieDomains });
            return r.rotated;
        }
        await applyProxyConfig(e, effectiveProxyUsername(e, settings, state), [webhookHost(settings)]);
        return true;
    }
    const r = await proxyRotate({ sessionId, settings, reason: "init", log, cookieDomains });
    return r.rotated;
}

/** After a manual captcha solve the current IP is trusted again. */
async function proxyClearCurrentCooldown(sessionId, settings) {
    const { entries } = parseProxyList(settings.proxyList || []);
    const state = await getProxyState(sessionId);
    if (state.idx >= 0 && state.idx < entries.length) {
        const es = state.entries[entries[state.idx].key];
        if (es) { delete es.cooldownUntil; await saveProxyState(sessionId, state); }
    }
}

/** Minutes until the first cooling proxy becomes usable again (0 if one is usable now). */
async function proxyMinutesUntilAvailable(sessionId, settings) {
    const { entries } = parseProxyList(settings.proxyList || []);
    if (entries.length === 0) return 0;
    const state = await getProxyState(sessionId);
    const now = Date.now();
    let soonest = Infinity;
    for (const e of entries) {
        const es = state.entries[e.key];
        if (!isCooling(es, now)) return 0;
        soonest = Math.min(soonest, es.cooldownUntil);
    }
    return Math.max(1, Math.ceil((soonest - now) / 60000));
}

async function proxyCountRequest(sessionId, settings) {
    const { entries } = parseProxyList(settings.proxyList || []);
    const state = await getProxyState(sessionId);
    state.requests = (state.requests || 0) + 1;
    if (state.idx >= 0 && state.idx < entries.length) {
        const k = entries[state.idx].key;
        const es = state.entries[k] || (state.entries[k] = { requests: 0, captchas: 0, fails: 0 });
        es.requests = (es.requests || 0) + 1;
    }
    await saveProxyState(sessionId, state);
    return state.requests;
}

async function proxyBudgetExceeded(sessionId, settings) {
    const budget = parseInt(settings.proxyBudget, 10) || 0;
    if (budget <= 0) return false;
    const state = await getProxyState(sessionId);
    return (state.requests || 0) >= budget;
}

// --- HEALTH CHECK ----------------------------------------------------------

async function getEchoUrls() {
    const data = await chrome.storage.local.get("rat_ip_echo_urls");
    return data.rat_ip_echo_urls || DEFAULT_IP_ECHO_URLS;
}

async function fetchThroughProxy(timeoutMs) {
    const urls = await getEchoUrls();
    let lastErr = "no echo service reachable";
    for (const url of urls) {
        const ctrl = new AbortController();
        const to = setTimeout(() => ctrl.abort(), timeoutMs);
        const t0 = Date.now();
        try {
            const r = await fetch(url, { signal: ctrl.signal, cache: "no-store" });
            if (!r.ok) { lastErr = `HTTP ${r.status}`; continue; }
            const j = await r.json();
            return { ok: true, ip: j.ip || "", country: j.country || "", ms: Date.now() - t0 };
        } catch (e) {
            lastErr = e.name === "AbortError" ? "timeout" : "connection or proxy authentication failed";
        } finally { clearTimeout(to); }
    }
    return { ok: false, error: lastErr };
}

/** Tests every proxy sequentially. The caller must make sure no scrape is running (global proxy setting). */
async function testProxies({ sessionId, settings, timeoutMs = 10000 }) {
    const { entries, errors } = parseProxyList(settings.proxyList || []);
    const state = await getProxyState(sessionId);
    const results = [];
    const testState = { ...state };
    const max = settings.proxyMode === "gateway" ? Math.min(entries.length, 3) : entries.length;

    for (let i = 0; i < max; i++) {
        const e = entries[i];
        testState.token = randomToken();
        await applyProxyConfig(e, effectiveProxyUsername(e, settings, testState), [webhookHost(settings)]);
        const r = await fetchThroughProxy(timeoutMs);
        const es = state.entries[e.key] || (state.entries[e.key] = { requests: 0, captchas: 0, fails: 0 });
        es.check = { ...r, at: Date.now() };
        results.push({ target: maskProxyForLog(e), ...r });
    }
    await clearProxyConfig();
    await saveProxyState(sessionId, state);
    return { results, errors: errors.map((x) => ({ line: x.raw.replace(/:[^:@]*@/, ":***@"), error: x.error })) };
}

async function proxyOverview(sessionId, settings) {
    const { entries } = parseProxyList(settings.proxyList || []);
    if (entries.length === 0) return null;
    const state = await getProxyState(sessionId);
    const now = Date.now();
    return {
        mode: settings.proxyMode || "list",
        current: state.idx,
        requestsOnCurrent: state.requests || 0,
        entries: entries.map((e) => {
            const es = state.entries[e.key] || {};
            return {
                target: maskProxyForLog(e),
                requests: es.requests || 0,
                captchas: es.captchas || 0,
                fails: es.fails || 0,
                coolingMinutes: isCooling(es, now) ? Math.ceil((es.cooldownUntil - now) / 60000) : 0,
                check: es.check || null
            };
        })
    };
}
