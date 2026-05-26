// IndexedDB helpers extracted from background.js – accept an `idb` instance
// so they can be tested with fake-indexeddb without touching the real browser DB.

const DB_NAME    = "RAT_Database";
const STORE_SESSIONS = "sessions";
const STORE_RESULTS  = "results";
const STORE_LOGS     = "logs";
const STORE_ENGINES  = "engines";

function openDB(idb) {
    return new Promise((resolve, reject) => {
        const request = idb.open(DB_NAME, 8);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_SESSIONS))
                db.createObjectStore(STORE_SESSIONS, { keyPath: "id" });
            if (!db.objectStoreNames.contains(STORE_RESULTS))
                db.createObjectStore(STORE_RESULTS);
            if (!db.objectStoreNames.contains(STORE_LOGS))
                db.createObjectStore(STORE_LOGS, { autoIncrement: true });
            if (!db.objectStoreNames.contains(STORE_ENGINES))
                db.createObjectStore(STORE_ENGINES, { keyPath: "engine.id" });
        };

        request.onsuccess  = (e) => resolve(e.target.result);
        request.onerror    = ()  => reject("DB Error");
    });
}

function saveSession(db, session) {
    const tx = db.transaction(STORE_SESSIONS, "readwrite");
    tx.objectStore(STORE_SESSIONS).put(session);
    return new Promise(r => tx.oncomplete = r);
}

function getSession(db, id) {
    return new Promise(r => {
        const tx  = db.transaction(STORE_SESSIONS, "readonly");
        const req = tx.objectStore(STORE_SESSIONS).get(id);
        req.onsuccess = () => r(req.result);
    });
}

function getAllSessions(db) {
    return new Promise(r => {
        const tx  = db.transaction(STORE_SESSIONS, "readonly");
        const req = tx.objectStore(STORE_SESSIONS).getAll();
        req.onsuccess = () => r(req.result);
    });
}

function deleteSession(db, id) {
    const tx = db.transaction(STORE_SESSIONS, "readwrite");
    tx.objectStore(STORE_SESSIONS).delete(id);
    return new Promise(r => tx.oncomplete = r);
}

function savePageContent(db, sessionId, taskIdx, pageNum, content) {
    const key = `${sessionId}_${taskIdx}_${pageNum}`;
    const tx  = db.transaction(STORE_RESULTS, "readwrite");
    tx.objectStore(STORE_RESULTS).put(content, key);
    return new Promise(r => tx.oncomplete = r);
}

function getPageContent(db, sessionId, taskIdx, pageNum) {
    const key = `${sessionId}_${taskIdx}_${pageNum}`;
    return new Promise(r => {
        const tx  = db.transaction(STORE_RESULTS, "readonly");
        const req = tx.objectStore(STORE_RESULTS).get(key);
        req.onsuccess = () => r(req.result);
    });
}

module.exports = { openDB, saveSession, getSession, getAllSessions, deleteSession, savePageContent, getPageContent };
