// Pure logic extracted from content.js for unit testing.
// No DOM, no chrome.*, no window.location, no sessionStorage dependencies.

/**
 * Decodes a result URL using the method specified in the engine config.
 * Currently supports "bing_base64" (Bing click-tracking redirect).
 */
function decodeUrl(url, method) {
    if (!url || url === "N/A") return "N/A";
    if (method === "bing_base64") {
        try {
            let urlObj = new URL(url);
            let uParam = urlObj.searchParams.get('u');
            if (uParam && uParam.startsWith('a1')) {
                let base64str = uParam.substring(2);
                while (base64str.length % 4 !== 0) base64str += '=';
                return decodeURIComponent(escape(atob(base64str.replace(/-/g, '+').replace(/_/g, '/'))));
            }
        } catch(e) {}
    }
    return url;
}

/**
 * Pure evaluation of CAPTCHA detection signals (no DOM access).
 * Extracted from isCaptchaPage() in content.js.
 *
 * Logic: urlIndicator alone is enough; text + selector together are enough.
 */
function evaluateCaptchaSignals(hasUrlIndicator, hasTextIndicator, hasSelector) {
    return hasUrlIndicator || (hasTextIndicator && hasSelector);
}

/**
 * Determines whether the current page is the first result page.
 * Extracted from initRankOffset() in content.js.
 *
 * @param {string|null} startParam - Raw value of URL ?start= (Google pagination)
 * @param {string|null} firstParam - Raw value of URL ?first= (Bing pagination, first page = "1")
 */
function computeIsFirstPage(startParam, firstParam) {
    return (!startParam || startParam === '0') && (!firstParam || firstParam === '1');
}

/**
 * Returns the rank offset that should be applied to organic results on the current page.
 * Extracted from initRankOffset() in content.js.
 *
 * @param {string}      currentQuery - Query string from the current URL
 * @param {string|null} lastQuery    - Previously stored query (from sessionStorage)
 * @param {boolean}     isFirstPage  - Whether this is the first result page
 * @param {string|null} storedCount  - Raw sessionStorage value for running organic count
 */
function computeRankOffset(currentQuery, lastQuery, isFirstPage, storedCount) {
    if (currentQuery !== lastQuery || isFirstPage) return 0;
    return storedCount ? parseInt(storedCount, 10) : 0;
}

module.exports = { decodeUrl, evaluateCaptchaSignals, computeIsFirstPage, computeRankOffset };
