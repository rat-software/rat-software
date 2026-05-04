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

module.exports = { generateUule, buildSearchUrl, getRandomDelay, parseProxyLine };
