/**
 * @file lib/human.js
 * Human-like pacing and trusted (isTrusted === true) input through the Chrome DevTools Protocol:
 * mouse paths, clicks, wheel scrolling and keyboard typing with typos.
 * Loaded into the service worker via importScripts().
 */

// --- RANDOMNESS / PACING -----------------------------------------------------

function rndInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function rndFloat(min, max) { return Math.random() * (max - min) + min; }

function gaussian() {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

/** Log-normal sample with the given median, clipped into [min, max]. Long right tail, like real dwell times. */
function lognormalMs(median, sigma, min, max) {
    const v = median * Math.exp(sigma * gaussian());
    return Math.round(Math.min(max, Math.max(min, v)));
}

/** Delay between min and max ms. "human" => log-normal with most mass in the lower third, uniform otherwise. */
function pacedDelay(minMs, maxMs, human) {
    if (maxMs <= minMs) return minMs;
    if (!human) return rndInt(minMs, maxMs);
    const median = minMs + (maxMs - minMs) * 0.3;
    return lognormalMs(median, 0.55, minMs, maxMs);
}

// --- CDP SESSION HANDLING ----------------------------------------------------

const cdpAttached = new Set();
const mousePos = new Map();

const CDP_TIMEOUT_MS = 15000;

let cdpDeadline = 0;
/** Caps the total time trusted input may take; afterwards every CDP call fails fast so the caller can fall back. 0 = no cap. */
function setCdpBudget(ms) { cdpDeadline = ms ? Date.now() + ms : 0; }

function cdpSend(tabId, method, params = {}) {
    return new Promise((resolve, reject) => {
        if (cdpDeadline && Date.now() > cdpDeadline) return reject(new Error("CDP time budget exceeded (window probably hidden or covered)"));
        const timer = setTimeout(() => reject(new Error(`CDP ${method} timed out (tab hidden or unresponsive)`)), CDP_TIMEOUT_MS);
        chrome.debugger.sendCommand({ tabId }, method, params, (res) => {
            clearTimeout(timer);
            if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
            else resolve(res);
        });
    });
}

function cdpAttach(tabId) {
    return new Promise((resolve, reject) => {
        if (cdpAttached.has(tabId)) return resolve(false);
        const timer = setTimeout(() => reject(new Error("CDP attach timed out")), CDP_TIMEOUT_MS);
        chrome.debugger.attach({ tabId }, "1.3", () => {
            clearTimeout(timer);
            if (chrome.runtime.lastError) {
                const m = chrome.runtime.lastError.message || "";
                if (m.includes("Another debugger is already attached")) return resolve(false);
                return reject(new Error(m));
            }
            cdpAttached.add(tabId);
            resolve(true);
        });
    });
}

function cdpDetach(tabId) {
    cdpAttached.delete(tabId);
    return new Promise((resolve) => {
        chrome.debugger.detach({ tabId }, () => { void chrome.runtime.lastError; resolve(); });
    });
}

chrome.debugger.onDetach.addListener((source) => { if (source.tabId) cdpAttached.delete(source.tabId); });
chrome.tabs.onRemoved.addListener((tabId) => { cdpAttached.delete(tabId); mousePos.delete(tabId); });

/** Runs fn(tabId) with the debugger attached; detaches again only if this call attached it. */
async function withCdp(tabId, fn) {
    // Occluded/background windows stall trusted input, so bring the tab's window to the front first.
    try {
        const t = await chrome.tabs.get(tabId);
        await chrome.windows.update(t.windowId, { focused: true });
        if (!t.active) await chrome.tabs.update(tabId, { active: true });
    } catch (e) { }
    const mine = await cdpAttach(tabId);
    try { return await fn(tabId); }
    finally { if (mine) await cdpDetach(tabId); }
}

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

// --- MOUSE -------------------------------------------------------------------

function bezierPoint(p0, p1, p2, p3, t) {
    const u = 1 - t;
    return {
        x: u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
        y: u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y
    };
}

async function cdpMouseMove(tabId, to) {
    const from = mousePos.get(tabId) || { x: rndInt(80, 400), y: rndInt(80, 300) };
    const dx = to.x - from.x, dy = to.y - from.y;
    const dist = Math.hypot(dx, dy);
    const steps = Math.max(8, Math.min(60, Math.round(dist / rndFloat(9, 16))));
    const bend = Math.min(180, dist * 0.35);
    const c1 = { x: from.x + dx * 0.25 + rndFloat(-bend, bend) * 0.5, y: from.y + dy * 0.25 + rndFloat(-bend, bend) * 0.5 };
    const c2 = { x: from.x + dx * 0.75 + rndFloat(-bend, bend) * 0.4, y: from.y + dy * 0.75 + rndFloat(-bend, bend) * 0.4 };
    for (let i = 1; i <= steps; i++) {
        const lin = i / steps;
        const t = lin < 0.5 ? 2 * lin * lin : 1 - Math.pow(-2 * lin + 2, 2) / 2; // ease-in-out
        const p = bezierPoint(from, c1, c2, to, t);
        await cdpSend(tabId, "Input.dispatchMouseEvent", {
            type: "mouseMoved", x: Math.round(p.x + (i < steps ? rndFloat(-0.8, 0.8) : 0)), y: Math.round(p.y + (i < steps ? rndFloat(-0.8, 0.8) : 0)), button: "none", buttons: 0
        });
        await delay(rndInt(5, 17));
    }
    mousePos.set(tabId, { x: to.x, y: to.y });
}

/** rect = {x, y, w, h} in viewport CSS pixels. Clicks a random point inside the central 60 % of the box. */
async function cdpClickRect(tabId, rect) {
    const target = {
        x: Math.round(rect.x + rect.w * rndFloat(0.2, 0.8)),
        y: Math.round(rect.y + rect.h * rndFloat(0.25, 0.75))
    };
    await cdpMouseMove(tabId, target);
    await delay(rndInt(60, 220));
    await cdpSend(tabId, "Input.dispatchMouseEvent", { type: "mousePressed", x: target.x, y: target.y, button: "left", buttons: 1, clickCount: 1 });
    await delay(rndInt(45, 140));
    await cdpSend(tabId, "Input.dispatchMouseEvent", { type: "mouseReleased", x: target.x, y: target.y, button: "left", buttons: 0, clickCount: 1 });
}

/** A few idle mouse movements across the page, like someone reading. */
async function cdpWander(tabId, viewport) {
    const w = viewport && viewport.w || 1200, h = viewport && viewport.h || 700;
    const n = rndInt(2, 4);
    for (let i = 0; i < n; i++) {
        await cdpMouseMove(tabId, { x: rndInt(Math.round(w * 0.15), Math.round(w * 0.85)), y: rndInt(Math.round(h * 0.15), Math.round(h * 0.8)) });
        await delay(rndInt(150, 900));
    }
}

/** Real wheel events (isTrusted). direction 1 = down, -1 = up. */
async function cdpWheelScroll(tabId, totalPx, direction = 1) {
    const pos = mousePos.get(tabId) || { x: rndInt(300, 700), y: rndInt(250, 450) };
    let done = 0;
    while (done < totalPx) {
        const d = Math.min(totalPx - done, rndInt(60, 150));
        await cdpSend(tabId, "Input.dispatchMouseEvent", {
            type: "mouseWheel", x: Math.round(pos.x), y: Math.round(pos.y), deltaX: 0, deltaY: d * direction
        });
        done += d;
        await delay(lognormalMs(70, 0.5, 25, 400));
        if (Math.random() < 0.06) await delay(rndInt(300, 1100));
    }
}

// --- KEYBOARD ----------------------------------------------------------------

const KEY_NEIGHBORS = {
    q: "wa", w: "qes", e: "wrd", r: "etf", t: "ryg", y: "tuh", u: "yij", i: "uok", o: "ipl", p: "ol",
    a: "qsz", s: "awdx", d: "serfc", f: "drtgv", g: "ftyhb", h: "gyujn", j: "huikm", k: "jiolm", l: "kop",
    z: "asx", x: "zsdc", c: "xdfv", v: "cfgb", b: "vghn", n: "bhjm", m: "njk"
};

function keyInfo(ch) {
    if (/[a-z]/i.test(ch)) { const up = ch.toUpperCase(); return { key: ch, code: "Key" + up, vk: up.charCodeAt(0) }; }
    if (/[0-9]/.test(ch)) return { key: ch, code: "Digit" + ch, vk: ch.charCodeAt(0) };
    if (ch === " ") return { key: " ", code: "Space", vk: 32 };
    return { key: ch, code: "", vk: 0 };
}

async function cdpPressChar(tabId, ch) {
    if (ch.charCodeAt(0) > 126 || ch.length > 1) {
        await cdpSend(tabId, "Input.insertText", { text: ch });
        return;
    }
    const k = keyInfo(ch);
    await cdpSend(tabId, "Input.dispatchKeyEvent", {
        type: "keyDown", key: k.key, code: k.code, text: ch, unmodifiedText: ch,
        windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk
    });
    await delay(rndInt(18, 70));
    await cdpSend(tabId, "Input.dispatchKeyEvent", {
        type: "keyUp", key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk
    });
}

async function cdpPressSpecial(tabId, name) {
    const map = {
        Enter: { key: "Enter", code: "Enter", vk: 13, text: "\r" },
        Backspace: { key: "Backspace", code: "Backspace", vk: 8 }
    };
    const k = map[name];
    const down = { type: k.text ? "keyDown" : "rawKeyDown", key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk };
    if (k.text) { down.text = k.text; down.unmodifiedText = k.text; }
    await cdpSend(tabId, "Input.dispatchKeyEvent", down);
    await delay(rndInt(20, 80));
    await cdpSend(tabId, "Input.dispatchKeyEvent", { type: "keyUp", key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk });
}

/** Types text into the currently focused element with human rhythm, occasional typos and corrections. */
async function cdpTypeText(tabId, text, opts = {}) {
    const typoChance = opts.typoChance !== undefined ? opts.typoChance : 0.025;
    const chars = Array.from(text);
    for (let i = 0; i < chars.length; i++) {
        const ch = chars[i];
        const lower = ch.toLowerCase();

        if (chars.length > 6 && i > 1 && KEY_NEIGHBORS[lower] && Math.random() < typoChance) {
            const wrongPool = KEY_NEIGHBORS[lower];
            let wrong = wrongPool[rndInt(0, wrongPool.length - 1)];
            if (ch !== lower) wrong = wrong.toUpperCase();
            await cdpPressChar(tabId, wrong);
            await delay(lognormalMs(220, 0.4, 120, 600));
            await cdpPressSpecial(tabId, "Backspace");
            await delay(lognormalMs(130, 0.4, 70, 350));
        }

        await cdpPressChar(tabId, ch);

        let gap = lognormalMs(105, 0.45, 40, 380);
        if (ch === " " && Math.random() < 0.25) gap += rndInt(80, 260);
        if (Math.random() < 0.03) gap += rndInt(400, 1200);
        if (i < chars.length - 1) await delay(gap);
    }
}
