// Pure logic extracted from sidepanel.js for unit testing.
// No DOM, no chrome.*, no localStorage dependencies.

const TASKS_PER_PAGE = 50;

// --- Task Filtering & Pagination ---

function filterTasks(tasks, filter) {
    if (filter === "ALL") return tasks;
    return tasks.filter(t => t.status === filter);
}

function paginateTasks(filtered, page, perPage = TASKS_PER_PAGE) {
    const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
    const safePage   = Math.max(1, Math.min(page, totalPages));
    const start      = (safePage - 1) * perPage;
    return {
        tasks:       filtered.slice(start, start + perPage),
        currentPage: safePage,
        totalPages,
    };
}

// --- Progress ---

function computeProgress(tasks) {
    return {
        done:  tasks.filter(t => t.status === "DONE").length,
        total: tasks.length,
    };
}

function computeProgressPercent(done, total) {
    if (total === 0) return 0;
    return (done / total) * 100;
}

// --- Status Display ---

function getStatusDisplay(status) {
    if (status === "PAUSED_CAPTCHA") return { text: "PAUSED (CAPTCHA)", color: "#dc3545" };
    return { text: status, color: "black" };
}

function getSessionCardClass(status) {
    if (status === "RUNNING")        return "session-card session-running";
    if (status === "PAUSED_CAPTCHA") return "session-card session-paused-captcha";
    return "session-card";
}

// --- Play/Pause Button State ---

function getPlayPauseBtnState(status) {
    if (status === "RUNNING") return { text: "Pause",          add: "btn-primary", remove: "btn-success" };
    return                           { text: "Resume / Start", add: "btn-success", remove: "btn-primary" };
}

// --- Task Item Visibility ---

function getTaskDeleteVisibility(status) {
    return (status === "OPEN" || status === "FAILED") ? "visible" : "hidden";
}

function getTaskRetryVisibility(status) {
    return status === "FAILED" ? "inline-block" : "none";
}

// --- Log Rendering ---

function getLogColor(level) {
    if (level === "WARN")  return "#856404";
    if (level === "ERROR") return "#721c24";
    return "#333";
}

// --- CSV Export ---

function escapeCSV(t) {
    return t ? `"${String(t).replace(/"/g, '""')}"` : '""';
}

function getExportFilename(sessionName) {
    return `RAT_Export_${sessionName.replace(/\W/g, '_')}.zip`;
}

// --- Zoom ---

function clampZoom(current, delta) {
    return Math.max(0.8, Math.min(2.0, current + delta));
}

// --- Query / Keyword Parsing ---

function parseQueries(text) {
    return text.split('\n').filter(x => x.trim());
}

function parseKeywordsFromFileContent(text) {
    return text.split(/[\r\n,;]+/).map(k => k.trim()).filter(k => k.length > 0);
}

// --- State Guards ---

function shouldUpdateStatus(dataSessionId, currentSessionId) {
    return dataSessionId === currentSessionId;
}

// --- Delay Conversion ---

function delaysToMs(minSec, maxSec) {
    return { min: minSec * 1000, max: maxSec * 1000 };
}

// --- Optimistic Task State Updates ---

function applyDeleteTask(cachedTasks, index) {
    const task = cachedTasks.find(t => t.index === index);
    if (task) task.status = "CANCELLED";
    return cachedTasks;
}

function applyRetryTask(cachedTasks, index) {
    const task = cachedTasks.find(t => t.index === index);
    if (task) { task.status = "OPEN"; task.retryCount = 0; }
    return cachedTasks;
}

module.exports = {
    filterTasks, paginateTasks,
    computeProgress, computeProgressPercent,
    getStatusDisplay, getSessionCardClass,
    getPlayPauseBtnState,
    getTaskDeleteVisibility, getTaskRetryVisibility,
    getLogColor,
    escapeCSV, getExportFilename,
    clampZoom,
    parseQueries, parseKeywordsFromFileContent,
    shouldUpdateStatus,
    delaysToMs,
    applyDeleteTask, applyRetryTask,
    TASKS_PER_PAGE,
};
