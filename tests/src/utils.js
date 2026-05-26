// Pure functions extracted from background.js for unit testing

function generateUule(loc) {
    const secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    return `w+CAIQICI${secret[loc.length % 65]}${btoa(loc)}`;
}

function buildSearchUrl(term, taskConfig, engineConfig) {
    const reqData = engineConfig.request;

    let u = reqData.baseUrl.replace("{domain}", taskConfig.domain || "");
    const urlObj = new URL(u);

    if (reqData.params.query) urlObj.searchParams.set(reqData.params.query, term);

    if (reqData.params.country && taskConfig.countryCode)
        urlObj.searchParams.set(reqData.params.country, taskConfig.countryCode);
    if (reqData.params.language && taskConfig.langCode)
        urlObj.searchParams.set(reqData.params.language, taskConfig.langCode);

    if (reqData.features && reqData.features.requiresUuleEncoding && taskConfig.location) {
        urlObj.searchParams.set(reqData.params.location, generateUule(taskConfig.location));
    }

    return urlObj.toString();
}

function getRandomDelay(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function parseProxyLine(line) {
    const parts = line.trim().split(':');
    if (parts.length !== 4) return null;
    const [ip, port, user, pass] = parts;
    const parsedPort = parseInt(port);
    if (isNaN(parsedPort)) return null;
    return { ip, port: parsedPort, user, pass };
}

// --- Proxy-Rotation Helpers ---

/** Parses the raw proxy textarea string into a filtered list of lines. */
function parseProxyList(str) {
    if (!str) return [];
    return str.split('\n').map(l => l.trim()).filter(l => l.length > 5);
}

/** Builds the Chrome proxy settings config object for a given IP/port. */
function buildProxyConfig(ip, port) {
    return {
        mode: "fixed_servers",
        rules: {
            singleProxy: { scheme: "http", host: ip, port: parseInt(port) },
            bypassList: ["localhost", "127.0.0.1"]
        }
    };
}

/** Selects a random entry from a proxy list. Returns null for empty lists. */
function selectRandomProxy(proxyList) {
    if (!proxyList || proxyList.length === 0) return null;
    return proxyList[Math.floor(Math.random() * proxyList.length)];
}

/** Returns the retry delay (in minutes) for a given retry count. */
function getRetryDelay(retryCount, delayList) {
    const level = Math.min(retryCount, delayList.length - 1);
    return delayList[level];
}

// --- Session Logic ---

/** Generates the full task list from a queries × configs cross-product. */
function buildTaskMatrix(queries, configs) {
    return queries.flatMap(q =>
        configs.map(conf => ({
            term: q, config: conf, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0,
        }))
    );
}

/** Returns true when the session is not actively running (mirrors isPaused in background.js). */
function isSessionPaused(session) {
    return !session || session.status !== "RUNNING";
}

/**
 * Increments retryCount and sets the next task status.
 * Returns "FAILED" once retryCount exceeds maxRetries, otherwise "RETRY".
 * Mutates the task object in place (mirrors handleRetry).
 */
function applyRetry(task, maxRetries = 3) {
    task.retryCount++;
    if (task.retryCount > maxRetries) {
        task.status = "FAILED";
        return "FAILED";
    }
    task.status = "OPEN";
    return "RETRY";
}

/**
 * Marks a non-DONE task as CANCELLED.
 * Returns false (and leaves the task untouched) when the task is already DONE.
 */
function applyCancelTask(task) {
    if (task.status === "DONE") return false;
    task.status = "CANCELLED";
    return true;
}

/** Resets a task back to its initial state for a clean re-run (mirrors resetSingleTask). */
function applyTaskReset(task) {
    task.status = "OPEN";
    task.retryCount = 0;
    task.pages = [];
    task.totalOrganic = 0;
    return task;
}

/**
 * Cancels all OPEN/FAILED tasks that belong to the given config.
 * Returns the number of tasks that were cancelled.
 */
function cancelTasksForConfig(tasks, configToRemove) {
    let cancelledCount = 0;
    tasks.forEach(task => {
        if (
            task.config.countryCode === configToRemove.countryCode &&
            task.config.langCode   === configToRemove.langCode &&
            task.config.domain     === configToRemove.domain
        ) {
            if (task.status === "OPEN" || task.status === "FAILED") {
                task.status = "CANCELLED";
                cancelledCount++;
            }
        }
    });
    return cancelledCount;
}

/** Builds the SESSION_STATUS broadcast payload (mirrors broadcastSessionStatus). */
function buildSessionStatusPayload(session, logs) {
    const current = session.tasks[session.currentIndex];
    return {
        sessionId:       session.id,
        name:            session.name,
        status:          session.status,
        progress: {
            done:  session.tasks.filter(t => t.status === "DONE").length,
            total: session.tasks.length,
        },
        currentQuery:    current ? `${current.term} (${current.config.engineName})` : "Done",
        logs:            logs || [],
        delays:          session.delays,
        originalConfigs: session.originalConfigs,
        originalQueries: session.originalQueries,
        settings:        session.settings,
        globalCount:     session.globalCount,
    };
}

module.exports = {
    generateUule, buildSearchUrl, getRandomDelay, parseProxyLine,
    parseProxyList, buildProxyConfig, selectRandomProxy, getRetryDelay,
    buildTaskMatrix, isSessionPaused, applyRetry, applyCancelTask,
    applyTaskReset, cancelTasksForConfig, buildSessionStatusPayload,
};
