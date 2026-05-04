/**
 * @file content.js - Version 2.4 (CSP Bugfix & Smart URLs)
 * Content script for the Result Assessment Tool (RAT).
 * Injected into SERPs to automate interactions and extract data
 * based on dynamic JSON configurations (Plugins).
 */

if (!window.ratListenerAdded) {
    window.ratListenerAdded = true;

    // --- CAPTCHA DETECTION ---
    function isCaptchaPage(config) {
        if (!config || !config.captcha) return false;
        
        const bodyText = document.body.innerText.toLowerCase();
        
        let hasUrlIndicator = config.captcha.urlIndicators.some(ind => window.location.href.toLowerCase().includes(ind));
        let hasTextIndicator = config.captcha.textIndicators.some(txt => bodyText.includes(txt));
        let hasSelector = config.captcha.selectors.some(sel => document.querySelector(sel) !== null);

        if (hasUrlIndicator || (hasTextIndicator && hasSelector)) {
            if (!window.captchaAlreadyLogged) {
                 console.warn(`🤖 RAT: CAPTCHA DETECTED by ${config.engine.name} rules!`);
                 window.captchaAlreadyLogged = true;
            }
            return true;
        }
        return false;
    }

    // --- MESSAGE LISTENER ---
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
        const config = msg.payload?.config;

        if (msg.action === "SCROLL_AND_PREPARE") {
            if (isCaptchaPage(config)) sendResponse({ success: false, isCaptcha: true });
            else performHumanActions(config).then(() => sendResponse({ success: true, isCaptcha: false }));
            return true;
        }
        
        if (msg.action === "SCRAPE_SERP") {
            if (isCaptchaPage(config)) sendResponse({ success: false, isCaptcha: true, data: null });
            else {
                const data = scrapeGenericData(config);
                sendResponse({ success: true, isCaptcha: false, data: data, html_content: document.documentElement.outerHTML });
            }
            return true;
        }
        
        if (msg.action === "NAVIGATE_NEXT") {
            if (isCaptchaPage(config)) sendResponse({ success: false, isCaptcha: true });
            else navigateToNext(config).then(sendResponse);
            return true;
        }
        
        if (msg.action === "GET_DIMENSIONS") {
            if (config && config.behavior && config.behavior.stickyHeaderSelectors) {
                const style = document.createElement('style');
                style.innerHTML = config.behavior.stickyHeaderSelectors.join(', ') + ` { position: absolute !important; }`;
                document.head.appendChild(style);
                void document.documentElement.offsetHeight;
            }
            sendResponse({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight, deviceScaleFactor: window.devicePixelRatio });
            return true;
        }
        
        if (msg.action === "CHECK_CAPTCHA") {
            sendResponse({ isCaptcha: isCaptchaPage(config) });
            return true;
        }
    });

    // --- ENHANCED HUMAN ACTIONS (GENERIC) ---
    async function performHumanActions(config) {
        console.log(`🤖 RAT: Starting Enhanced Human Sequence for ${config.engine.name}...`);

        if (config.behavior.cookieConsentSelectors) {
            for (let sel of config.behavior.cookieConsentSelectors) {
                let btn = document.querySelector(sel);
                if (btn) { btn.click(); await wait(800); break; }
            }
        }
        
        if (config.behavior.popupDismissSelectors && config.behavior.popupDismissSelectors.length > 0) {
            for (let i = 0; i < 2; i++) {
                let clicked = false;
                for (let sel of config.behavior.popupDismissSelectors) {
                    let dlgs = document.querySelectorAll(sel);
                    for (let dlg of dlgs) {
                        if (dlg.offsetParent === null) continue;
                        let btns = dlg.querySelectorAll('button, [role="button"]');
                        for (let btn of btns) {
                            let text = (btn.innerText || "").toLowerCase().trim();
                            if (config.behavior.popupDismissKeywords && config.behavior.popupDismissKeywords.some(k => k.length < 4 ? text === k : text.includes(k))) {
                                try { btn.click(); clicked = true; break; } catch(e) {}
                            }
                        }
                        if (clicked) break;
                    }
                }
                if (clicked) { await wait(1500); break; }
                await wait(300);
            }
        }

        const totalHeight = () => document.body.scrollHeight;
        let currentY = 0;
        
        while (currentY < totalHeight()) {
            currentY += Math.floor(Math.random() * 250) + 100;
            window.scrollTo({ top: currentY, behavior: 'smooth' }); 
            await wait(Math.floor(Math.random() * 300) + 100);
            if ((window.innerHeight + window.scrollY) >= totalHeight() - 50) break;
        }

        await wait(1200);
        window.scrollTo({ top: 0, behavior: 'smooth' }); 
        await wait(1500);

        if (config.behavior.aiExpandSelectors) {
            for (let sel of config.behavior.aiExpandSelectors) {
                let attempts = 0;
                while (attempts < 10) {
                    attempts++;
                    let btn = document.querySelector(`${sel}:not([data-rat-clicked])`);
                    if (!btn) break; 
                    
                    btn.setAttribute('data-rat-clicked', 'true'); 
                    if (btn.offsetParent === null) continue; 

                    if (config.behavior.aiExpandKeywords && config.behavior.aiExpandKeywords.length > 0) {
                        let text = (btn.innerText || btn.getAttribute('aria-label') || btn.title || "").toLowerCase().trim();
                        let match = config.behavior.aiExpandKeywords.some(k => text === k.toLowerCase() || text.includes(k.toLowerCase()));
                        if (!match) continue; 
                    }

                    try {
                        btn.scrollIntoView({ block: "center", behavior: "smooth" });
                        await wait(600);
                        
                        const anchor = btn.tagName === 'A' ? btn : btn.closest('a');
                        if (anchor && (anchor.getAttribute('href') || '').toLowerCase().startsWith('javascript:')) {
                            anchor.removeAttribute('href');
                        }
                        
                        // Sicheres MouseEvent anstelle von .click()
                        btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        
                        await wait(1500);
                    } catch (err) {
                        console.warn(`🤖 RAT: Ignored error while clicking AI button.`, err);
                    }
                }
            }
        }
    }

    // --- UTILS ---
    function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

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

    function initRankOffset(queryParamName) {
        const urlParams = new URLSearchParams(window.location.search);
        const currentQuery = urlParams.get(queryParamName) || "";
        const isFirstPage = (!urlParams.get('start') || urlParams.get('start') === '0') && (!urlParams.get('first') || urlParams.get('first') === '1');
        
        const STORAGE_KEY_QUERY = "rat_last_query";
        const STORAGE_KEY_COUNT = "rat_organic_count";
        const lastQuery = sessionStorage.getItem(STORAGE_KEY_QUERY);

        let rankOffset = 0;
        if (currentQuery !== lastQuery || isFirstPage) {
            sessionStorage.setItem(STORAGE_KEY_QUERY, currentQuery);
            sessionStorage.setItem(STORAGE_KEY_COUNT, "0");
        } else {
            const storedCount = sessionStorage.getItem(STORAGE_KEY_COUNT);
            if (storedCount) rankOffset = parseInt(storedCount, 10);
        }
        return rankOffset;
    }

    // --- GENERIC SCRAPER ---
    function scrapeGenericData(config) {
        const result = { organic: [], ads: [], ai_overview: { found: false, text_full: "", sources: [] } };
        let rankOffset = initRankOffset(config.request.params.query);
        const decodeMethod = config.request.features.urlDecodingMethod;
        const selConfig = config.selectors;

        // 1. Process AI Overview
        const aiContainer = document.querySelector(selConfig.ai_overview.container);
        if (aiContainer) {
            let cleanText = "";
            let textConfig = selConfig.ai_overview.text;
            
            if (textConfig) {
                let textNode = document.querySelector(textConfig.selector) || aiContainer;
                const clone = textNode.cloneNode(true);
                
                if (textConfig.elementsToRemove) {
                    clone.querySelectorAll(textConfig.elementsToRemove.join(', ')).forEach(el => el.remove());
                }
                cleanText = clone.innerText.replace(/\r\n|\r|\n/g, '\r\n').replace(/(\r\n){4,}/g, '\r\n\r\n\r\n').trim();
                
                if (textConfig.regexClean) {
                    cleanText = cleanText.replace(new RegExp(textConfig.regexClean, 'g'), '').trim();
                }
            }

            const uniqueUrls = new Set();
            
            if (Array.isArray(selConfig.ai_overview.sources)) {
                selConfig.ai_overview.sources.forEach(srcRule => {
                    document.querySelectorAll(srcRule.container).forEach(el => {
                        let url = "", title = "Source";
                        
                        if (srcRule.type === "attribute_based") {
                            url = decodeUrl(el.getAttribute(srcRule.urlAttribute) || '', decodeMethod);
                            title = el.getAttribute(srcRule.titleAttribute) || "Source";
                        } else {
                            let linkEl = el.querySelector(srcRule.url) || (el.tagName === 'A' ? el : el.querySelector('a'));
                            if (linkEl) url = decodeUrl(linkEl.href, decodeMethod);
                            let titleEl = srcRule.title ? el.querySelector(srcRule.title) : null;
                            title = titleEl ? titleEl.innerText.trim() : (linkEl ? (linkEl.getAttribute('aria-label') || linkEl.innerText.trim()) : "Source");
                        }

                        if (url && url !== "N/A" && !url.includes(config.request.baseUrl.split('/')[2]) && !uniqueUrls.has(url)) {
                            result.ai_overview.sources.push({ title: title, url: url });
                            uniqueUrls.add(url);
                        }
                    });
                });
            }

            if (cleanText || result.ai_overview.sources.length > 0) {
                result.ai_overview.found = true;
                result.ai_overview.text_full = cleanText;
            }
        }

        // 2. Process Organic Results and Ads
        const mainArea = selConfig.organic.mainCol ? document.querySelector(selConfig.organic.mainCol) : document;
        if (mainArea) {
            const allItems = mainArea.querySelectorAll(`${selConfig.organic.container}, ${selConfig.ads.container}`);
            
            for (let item of allItems) {
                if (item.offsetHeight === 0 || !item.innerText.trim()) continue;
                
                if (selConfig.organic.excludeContainers && selConfig.organic.excludeContainers.some(ex => item.matches(ex) || item.querySelector(ex))) continue;

                const isAd = item.matches(selConfig.ads.container);
                const rule = isAd ? selConfig.ads : selConfig.organic;
                
                const titleEl = item.querySelector(rule.title);
                
                let linkEl = null;
                if (titleEl) {
                    if (titleEl.tagName === 'A') linkEl = titleEl;
                    else linkEl = titleEl.querySelector('a');
                }
                if (!linkEl && rule.url) linkEl = item.querySelector(rule.url);
                if (!linkEl) linkEl = item.querySelector('a');
                
                if (!linkEl) continue;
                
                const url = decodeUrl(linkEl.href, decodeMethod);
                
                if (!url || url === "N/A" || (url.includes(config.request.baseUrl.split('/')[2]) && !url.includes('/ck/a'))) continue;

                const title = titleEl ? titleEl.innerText.trim() : linkEl.innerText.trim();
                
                let snippet = "";
                if (rule.snippet.selector === "inner_text") {
                    snippet = item.innerText.substring(0, rule.snippet.maxLength || 200).replace(/\n/g, " ");
                } else {
                    const blocks = item.querySelectorAll(rule.snippet.selector);
                    for (let b of blocks) {
                        if ((!rule.snippet.minLength || b.innerText.length > rule.snippet.minLength) && !b.innerText.includes(title)) { 
                            snippet = b.innerText.trim(); break; 
                        }
                    }
                }

                if (isAd) {
                    result.ads.push({ rank: result.ads.length + 1, title: title, url: url, snippet: snippet });
                } else {
                    result.organic.push({ rank: rankOffset + result.organic.length + 1, title: title, url: url, snippet: snippet });
                }
            }
        }
        sessionStorage.setItem("rat_organic_count", (rankOffset + result.organic.length).toString());
        return result;
    }

    // --- NAVIGATION ---
    async function navigateToNext(config) {
        let nextBtn = document.querySelector(config.selectors.pagination.nextButton);
        
        if (!nextBtn && config.selectors.pagination.fallbackActiveSibling) {
             const activePage = document.querySelector(config.selectors.pagination.fallbackActiveSibling);
             if (activePage && activePage.nextElementSibling) nextBtn = activePage.nextElementSibling.querySelector('a');
        }
        
        if (!nextBtn && config.selectors.pagination.fallbackUrlMath) {
            const match = window.location.href.match(new RegExp(config.selectors.pagination.fallbackUrlMath));
            let nextStart = match ? parseInt(match[1]) + 10 : 10;
            nextBtn = document.querySelector(`a[href*="start=${nextStart}"]`);
        }

        if (nextBtn) {
            nextBtn.scrollIntoView({ block: "center", behavior: "smooth" });
            await wait(1000); 
            nextBtn.click();
            return { success: true };
        }
        return { success: false };
    }
}