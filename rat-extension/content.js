/**
 * @file content.js - Version 2.4 (Infinite Scroll State Fix)
 * Content script for the Result Assessment Tool (RAT).
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
                const data = scrapeGenericData(config, msg.payload.startRank);
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

    // --- ENHANCED HUMAN ACTIONS ---
    async function performHumanActions(config) {
        console.log(`🤖 RAT: Starting Enhanced Human Sequence for ${config.engine.name}...`);

        // 1. Aggressive Cookie Banner Dismissal
        if (config.behavior.cookieConsentSelectors) {
            for (let sel of config.behavior.cookieConsentSelectors) {
                let btns = document.querySelectorAll(sel);
                for (let btn of btns) {
                    if (btn && btn.offsetParent !== null) { 
                        try { btn.click(); await wait(800); } catch(e) {} 
                    }
                }
            }
            if (window.location.href.includes("youtube.com")) {
                let allBtns = document.querySelectorAll('button, yt-button-shape');
                for (let b of allBtns) {
                    let txt = (b.innerText || "").toLowerCase();
                    if ((txt.includes("alle akzeptieren") || txt.includes("accept all")) && b.offsetParent !== null) {
                        try { b.click(); await wait(800); } catch(e) {}
                    }
                }
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

        // 2. Multi-Container Scroll Simulation (Fixed state for Infinite Scroll)
        const getDocHeight = () => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        
        // Starte Scroll dort, wo wir zuletzt waren (wichtig für nachladende Ergebnisse!)
        let currentY = window.scrollY || 0;
        let maxScrollSteps = 10; 
        
        while (currentY < getDocHeight() && maxScrollSteps > 0) {
            currentY += Math.floor(Math.random() * 500) + 300;
            window.scrollTo({ top: currentY, behavior: 'smooth' }); 
            
            document.querySelectorAll('#page-manager, ytd-app, #content, ytd-search').forEach(el => {
                if (el.scrollHeight > el.clientHeight) {
                    try { el.scrollBy({top: 400, behavior: 'smooth'}); } catch(e) {}
                }
            });

            await wait(Math.floor(Math.random() * 300) + 200);
            maxScrollSteps--; 
        }

        await wait(1200);
        
        // Zurück zum Anfang scrollen nur, wenn es KEIN Infinite Scroll ist!
        if (!config.selectors.pagination || config.selectors.pagination.type !== "infinite_scroll") {
            window.scrollTo({ top: 0, behavior: 'smooth' }); 
            await wait(1500);
        }

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
                        
                        btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        await wait(1500);
                    } catch (err) {}
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

    function isValidSourceUrl(url, config) {
        if (!url || typeof url !== 'string') return false;
        url = url.trim();
        if (!url.startsWith('http') && !url.startsWith('/')) return false;
        if (url.includes('favicon')) return false;
        if (url.includes('gstatic.com')) return false;
        if (url.includes('google.com/search')) return false;
        
        try {
            let u = new URL(url, window.location.origin);
            let hostname = u.hostname.replace(/^www\./, '');
            
            let engineHostname = "google.com";
            if (config && config.request && config.request.baseUrl) {
                engineHostname = new URL(config.request.baseUrl.replace("{domain}", "google.com")).hostname.replace(/^www\./, '');
            }

            if ((hostname === engineHostname || hostname.includes('google.') || hostname.includes('bing.')) && (u.pathname === '/' || u.pathname === '')) {
                return false;
            }
        } catch(e) { return false; }

        return true;
    }

    function getCleanDomainAndPath(urlString) {
        try {
            let u = new URL(urlString, window.location.origin);
            let clean = u.hostname.replace(/^www\./, '') + u.pathname;
            
            if (clean.includes('youtube.com/watch') && u.searchParams.has('v')) {
                clean += '?v=' + u.searchParams.get('v');
            }
            return clean.replace(/\/$/, '');
        } catch(e) {
            return urlString.replace(/^https?:\/\/(www\.)?/, '').split('?')[0].split('#')[0].replace(/\/$/, '');
        }
    }

    function extractFormattedPlainText(rawHtml) {
        if (!rawHtml) return "";
        const parser = new DOMParser();
        const doc = parser.parseFromString(rawHtml, 'text/html');
        let text = "";

        function walkDOM(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                text += node.textContent.replace(/\s+/g, ' ');
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const tag = node.tagName.toUpperCase();
                if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG'].includes(tag)) return; 
                if (tag === 'LI') text += '\n• ';

                node.childNodes.forEach(child => walkDOM(child));

                if (['P', 'H1', 'H2', 'H3', 'H4', 'BR', 'UL', 'OL', 'DIV'].includes(tag)) {
                    text += '\n\n';
                }
            }
        }

        doc.body.childNodes.forEach(child => walkDOM(child));
        text = text.replace(/•[ \t]*(?=\n|$)/g, '');
        text = text.replace(/\n{3,}/g, '\n\n');
        return text.trim();
    }

    function extractSegmentedText(rawHtml, inlineConfig, config) {
        if (!rawHtml) return [];
        const parser = new DOMParser();
        const doc = parser.parseFromString(rawHtml, 'text/html');
        
        let segments = [];
        let currentText = "";
        let currentCitations = [];

        function walkDOM(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                let textFragment = node.textContent.replace(/\s+/g, ' ');
                if (textFragment.trim().length > 0 && currentCitations.length > 0) {
                    segments.push({ text: currentText, citations: [...currentCitations] });
                    currentText = ""; currentCitations = [];
                }
                currentText += textFragment;
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const tag = node.tagName.toUpperCase();
                if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG'].includes(tag)) return; 

                if (inlineConfig && inlineConfig.selector && node.matches(inlineConfig.selector)) {
                    let citeText = node.textContent.replace(/\s+/g, ' ').trim();
                    
                    let uuid = null;
                    if (inlineConfig.dataAttribute && node.hasAttribute(inlineConfig.dataAttribute)) {
                        uuid = node.getAttribute(inlineConfig.dataAttribute);
                    }
                    if (!uuid) {
                        uuid = node.getAttribute('data-icl-uuid');
                        if (!uuid) {
                            let innerUuidNode = node.querySelector('[data-icl-uuid]');
                            if (innerUuidNode) uuid = innerUuidNode.getAttribute('data-icl-uuid');
                        }
                    }

                    let url = null;
                    if (inlineConfig.urlAttribute && node.hasAttribute(inlineConfig.urlAttribute)) {
                        url = node.getAttribute(inlineConfig.urlAttribute);
                    }
                    if (!url) {
                        url = node.getAttribute('href') || node.getAttribute('data-url');
                        if (!url) {
                            let innerLink = node.querySelector('a[href], a[data-url]');
                            if (innerLink) url = innerLink.getAttribute('href') || innerLink.getAttribute('data-url');
                        }
                    }
                    
                    currentCitations.push({ text: citeText, url: url || null, uuid: uuid || null, isMedia: false });
                    return; 
                }

                if (tag === 'A' && node.hasAttribute('href')) {
                    let url = node.getAttribute('href');
                    if (isValidSourceUrl(url, config) && node.closest('.xrOenc, .ktTVvf, .ZldSN')) {
                        let titleNode = node.querySelector('.Pcfhk, .VfPpkd-mRLv6, h3, .vv-title, [role="heading"]');
                        let mediaTitle = titleNode ? titleNode.textContent.trim() : node.textContent.replace(/\s+/g, ' ').trim();
                        if (!mediaTitle) mediaTitle = "Media Element";
                        
                        node.childNodes.forEach(child => walkDOM(child));
                        currentCitations.push({ text: mediaTitle, url: url, uuid: null, isMedia: true });
                        return;
                    }
                }

                if (tag === 'LI') {
                    if (currentCitations.length > 0) {
                        segments.push({ text: currentText, citations: [...currentCitations] });
                        currentText = ""; currentCitations = [];
                    }
                    currentText += '\n• ';
                }

                node.childNodes.forEach(child => walkDOM(child));

                if (['P', 'H1', 'H2', 'H3', 'H4', 'BR', 'UL', 'OL', 'DIV'].includes(tag)) {
                    if (currentCitations.length > 0) {
                        segments.push({ text: currentText, citations: [...currentCitations] });
                        currentText = ""; currentCitations = [];
                    }
                    currentText += '\n\n';
                }
            }
        }

        doc.body.childNodes.forEach(child => walkDOM(child));
        
        if (currentText.trim().length > 0 || currentCitations.length > 0) {
            segments.push({ text: currentText, citations: [...currentCitations] });
        }
        
        segments.forEach(seg => {
            seg.text = seg.text.replace(/•[ \t]*(?=\n|$)/g, '').replace(/\n{3,}/g, '\n\n').trim();
        });

        return segments.filter(seg => seg.text !== "" || seg.citations.length > 0);
    }

    // --- GENERIC SCRAPER ---
    function scrapeGenericData(config, passedStartRank) {
        const result = { organic: [], ads: [], images: [], videos: [], ai_overview: { found: false, text_full: "", sources: [], segments: [] } };
        let rankOffset = passedStartRank !== undefined ? passedStartRank : initRankOffset(config.request.params.query);
        const decodeMethod = config.request.features.urlDecodingMethod;
        const selConfig = config.selectors;

        let uuidToUrls = new Map();
        
        function decodeHTMLEntities(text) {
            let t = document.createElement('textarea');
            t.innerHTML = text;
            return t.value;
        }

        function processParsed(item) {
            if (Array.isArray(item)) {
                if (item.length >= 2 && typeof item[0] === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(item[0])) {
                    let uuid = item[0];
                    let urls = findUrlsInArray(item);
                    urls.forEach(url => {
                        if (!uuidToUrls.has(uuid)) uuidToUrls.set(uuid, new Set());
                        uuidToUrls.get(uuid).add(url);
                    });
                }
                item.forEach(subItem => { if (Array.isArray(subItem)) processParsed(subItem); });
            }
        }
        
        function findUrlsInArray(arr) {
            let urls = [];
            for (let i = 0; i < arr.length; i++) {
                let val = arr[i];
                if (typeof val === 'string') {
                    if (isValidSourceUrl(val, config)) urls.push(val);
                } else if (Array.isArray(val)) {
                    urls.push(...findUrlsInArray(val));
                }
            }
            return urls;
        }

        const treeWalker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_COMMENT, null, false);
        let currentNode = treeWalker.nextNode();
        const commentRegex = /TgQPHd[\s\S]*?\|(\[.*\])/; 
        
        while(currentNode) {
            let commentText = currentNode.nodeValue || "";
            let match = commentText.match(commentRegex);
            if (match) {
                try {
                    let jsonString = decodeHTMLEntities(match[1]);
                    let parsed = JSON.parse(jsonString);
                    processParsed(parsed);
                } catch(e) { } 
            }
            currentNode = treeWalker.nextNode();
        }

        // 1. Process AI Overview
        if (selConfig.ai_overview && selConfig.ai_overview.container) {
            const aiContainer = document.querySelector(selConfig.ai_overview.container);
            if (aiContainer) {
                result.ai_overview.found = true;
                const tempSources = new Map();

                if (selConfig.ai_overview.sources) {
                    selConfig.ai_overview.sources.forEach(srcRule => {
                        const sourceElements = document.querySelectorAll(srcRule.container);
                        
                        sourceElements.forEach(el => {
                            let organicContainerSelector = selConfig.organic?.container || null;
                            if (organicContainerSelector && el.closest(organicContainerSelector)) return; 
                            
                            let linkEl = null, url = "";
                            
                            if (srcRule.type === "attribute_based") {
                                url = decodeUrl(el.getAttribute(srcRule.urlAttribute) || '', decodeMethod);
                                let title = el.getAttribute(srcRule.titleAttribute) || "Source";
                                if (isValidSourceUrl(url, config)) {
                                    tempSources.set(getCleanDomainAndPath(url), { title: title, url: url, type: "carousel" });
                                }
                                return;
                            }

                            if (srcRule.url) {
                                const urlSelectors = srcRule.url.split(',').map(s => s.trim());
                                for (let selector of urlSelectors) {
                                    let found = el.matches(selector) ? el : el.querySelector(selector);
                                    if (found && (found.href || found.getAttribute('data-url'))) {
                                        linkEl = found;
                                        url = found.href || found.getAttribute('data-url');
                                        break; 
                                    }
                                }
                            }
                            
                            if (!linkEl) {
                                linkEl = el.tagName === 'A' ? el : el.querySelector('a');
                                if (linkEl) url = linkEl.href || linkEl.getAttribute('data-url');
                            }

                            url = decodeUrl(url, decodeMethod);
                            if (!isValidSourceUrl(url, config)) return;

                            let title = ""; let bestLabel = "";
                            const labelCandidates = [el, ...el.querySelectorAll('[aria-label]')];
                            
                            for (let candidate of labelCandidates) {
                                let tempLabel = candidate.getAttribute('aria-label');
                                if (tempLabel) {
                                    let isUiButton = tempLabel.toLowerCase().includes("informationen") || tempLabel.toLowerCase().includes("information") || tempLabel.toLowerCase().includes("about this");
                                    if (!isUiButton && tempLabel.length > bestLabel.length) bestLabel = tempLabel;
                                }
                            }

                            if (bestLabel) {
                                title = bestLabel.replace(/\.?\s*(Wird in einem neuen Tab geöffnet|Opens in a new tab)\.?/gi, "");
                                title = title.trim().replace(/[\s\-\|·•]+$/, "");
                            }

                            if (!title || title.length < 3) {
                                let titleEl = srcRule.title ? el.querySelector(srcRule.title) : null;
                                title = titleEl ? titleEl.textContent.trim() : linkEl.textContent.trim();
                            }

                            let domainFallback = "";
                            try { domainFallback = new URL(url, window.location.origin).hostname.replace(/^www\./, ''); } catch(e) { domainFallback = "Source"; }
                            if (!title || title.length < 3) title = domainFallback;

                            let cleanKey = getCleanDomainAndPath(url);
                            let existing = tempSources.get(cleanKey);
                            
                            let currentIsDomain = (title.toLowerCase() === domainFallback.toLowerCase()) || title === "Source";
                            let existingIsDomain = existing ? ((existing.title.toLowerCase() === domainFallback.toLowerCase()) || existing.title === "Source") : false;

                            let shouldUpdate = false;
                            if (!existing) shouldUpdate = true;
                            else if (existingIsDomain && !currentIsDomain) shouldUpdate = true; 
                            else if (currentIsDomain === existingIsDomain && title.length > existing.title.length) shouldUpdate = true; 

                            if (shouldUpdate) {
                                tempSources.set(cleanKey, { title: title, url: url, type: "carousel" });
                            }
                        });
                    });

                    let idCounter = 1;
                    for (let [key, data] of tempSources.entries()) {
                        result.ai_overview.sources.push({
                            id: idCounter++, title: data.title, url: data.url, type: data.type || "carousel"
                        });
                    }
                }

                let textConfig = selConfig.ai_overview.text;
                if (textConfig) {
                    let textNode = document.querySelector(textConfig.selector) || aiContainer;
                    let clone = textNode.cloneNode(true);
                    
                    let inlineConfig = selConfig.ai_overview.inline_citations || { selector: selConfig.ai_overview.inlineCitationSelector };
                    result.ai_overview.segments = extractSegmentedText(clone.innerHTML, inlineConfig, config);

                    if (textConfig.elementsToRemove && textConfig.elementsToRemove.length > 0) {
                        clone.querySelectorAll(textConfig.elementsToRemove.join(', ')).forEach(e => e.remove());
                    }
                    
                    let textFull = extractFormattedPlainText(clone.innerHTML);
                    if (textConfig.regexClean) {
                        textFull = textFull.replace(new RegExp(textConfig.regexClean, 'g'), '').trim();
                    }
                    result.ai_overview.text_full = textFull;
                }

                if (result.ai_overview.segments.length > 0) {
                    result.ai_overview.segments.forEach(seg => {
                        let matchedCitationIds = new Set(); 

                        seg.citations.forEach(cit => {
                            if (cit.uuid && /^[0-9,\s]+$/.test(cit.uuid)) {
                                cit.uuid.split(',').forEach(numStr => {
                                    let idNum = parseInt(numStr.trim(), 10);
                                    if (!isNaN(idNum)) {
                                        let matchedSource = result.ai_overview.sources.find(s => s.id === idNum);
                                        if (matchedSource) matchedCitationIds.add(matchedSource.id);
                                    }
                                });
                            }

                            let urlsToMatch = new Set();
                            let decodedCitUrl = decodeUrl(cit.url, decodeMethod);
                            if (isValidSourceUrl(decodedCitUrl, config)) {
                                urlsToMatch.add(decodedCitUrl.trim());
                            }
                            
                            if (cit.uuid && uuidToUrls.has(cit.uuid)) {
                                uuidToUrls.get(cit.uuid).forEach(u => urlsToMatch.add(decodeUrl(u, decodeMethod)));
                            }
                            
                            let sortedUrls = Array.from(urlsToMatch).sort((a, b) => b.length - a.length);
                            let validTargetUrls = [];
                            let domainToPathCount = new Map();

                            sortedUrls.forEach(u => {
                                try {
                                    let urlObj = new URL(u, window.location.origin);
                                    let domain = urlObj.hostname.replace(/^www\./, '');
                                    let path = urlObj.pathname;
                                    if (path && path !== '/') {
                                        validTargetUrls.push(u);
                                        domainToPathCount.set(domain, (domainToPathCount.get(domain) || 0) + 1);
                                    } else {
                                        if (!domainToPathCount.has(domain)) {
                                            validTargetUrls.push(u);
                                            domainToPathCount.set(domain, 1);
                                        }
                                    }
                                } catch(e) { validTargetUrls.push(u); }
                            });

                            validTargetUrls.forEach(targetUrl => {
                                let cleanCit = getCleanDomainAndPath(targetUrl);
                                let matchedSource = result.ai_overview.sources.find(s => getCleanDomainAndPath(s.url) === cleanCit);
                                if (!matchedSource) {
                                    matchedSource = result.ai_overview.sources.find(s => {
                                        let cleanSrc = getCleanDomainAndPath(s.url);
                                        return cleanSrc.includes(cleanCit) || cleanCit.includes(cleanSrc);
                                    });
                                }
                                
                                if (matchedSource) {
                                    matchedCitationIds.add(matchedSource.id);
                                } else {
                                    let newId = result.ai_overview.sources.length + 1;
                                    let newTitle = "Inline Source";
                                    let sourceType = "inline";

                                    if (cit.isMedia) {
                                        newTitle = cit.text && cit.text !== "Media Element" ? cit.text : "Embedded Video";
                                        sourceType = "media";
                                    } else if (cit.text && cit.text.length > 2) {
                                        newTitle = cit.text;
                                    }

                                    if (newTitle === "Inline Source" || newTitle === "Embedded Video") {
                                        try { newTitle = new URL(targetUrl, window.location.origin).hostname.replace(/^www\./, ''); } catch(e){}
                                    }

                                    result.ai_overview.sources.push({ 
                                        id: newId, title: newTitle, url: targetUrl, type: sourceType 
                                    });
                                    matchedCitationIds.add(newId);
                                }
                            });
                        });
                        seg.citations = Array.from(matchedCitationIds).sort((a, b) => a - b);
                    });
                }
            }
        }

        // 2. Process Organic, Images, Videos, and Ads
        const mainArea = selConfig.organic?.mainCol ? document.querySelector(selConfig.organic.mainCol) : 
                         selConfig.images?.mainCol ? document.querySelector(selConfig.images.mainCol) : document;

        if (mainArea) {
            const querySelectors = [];
            if (selConfig.organic?.container) querySelectors.push(selConfig.organic.container);
            if (selConfig.images?.container) querySelectors.push(selConfig.images.container);
            if (selConfig.videos?.container) querySelectors.push(selConfig.videos.container);
            if (selConfig.ads?.container) querySelectors.push(selConfig.ads.container);

            if (querySelectors.length > 0) {
                const allItems = mainArea.querySelectorAll(querySelectors.join(', '));
                
                for (let item of allItems) {
                    
                    const rect = item.getBoundingClientRect();
                    if (rect.height === 0 && rect.width === 0 && (!item.innerText || item.innerText.trim() === "")) continue;

                    let rule = null;
                    let type = "";
                    
                    if (selConfig.ads?.container && item.matches(selConfig.ads.container)) {
                        rule = selConfig.ads;
                        type = "ad";
                    } else if (selConfig.videos?.container && item.matches(selConfig.videos.container)) {
                        rule = selConfig.videos;
                        type = "video";
                    } else if (selConfig.images?.container && item.matches(selConfig.images.container)) {
                        rule = selConfig.images;
                        type = "image";
                        if (selConfig.images.excludeContainers && selConfig.images.excludeContainers.some(ex => item.matches(ex) || item.querySelector(ex))) continue;
                    } else if (selConfig.organic?.container && item.matches(selConfig.organic.container)) {
                        rule = selConfig.organic;
                        type = "organic";
                        if (selConfig.organic.excludeContainers && selConfig.organic.excludeContainers.some(ex => item.matches(ex) || item.querySelector(ex))) continue;
                    }
                    
                    if (!rule) continue;
                    
					const titleEl = rule.title ? item.querySelector(rule.title) : null;
					let linkEl = null;

					// 1. Link aus Titel extrahieren (mit fallback auf das umschließende <a> Element)
					if (titleEl) {
						if (titleEl.tagName === 'A') linkEl = titleEl;
						else linkEl = titleEl.querySelector('a') || titleEl.closest('a');
					}

					// 2. Link aus URL-Selektor extrahieren (falls Titel kein Link war)
					if (!linkEl && rule.url) {
						let temp = item.querySelector(rule.url);
						if (temp) {
							if (temp.tagName === 'A') linkEl = temp;
							else linkEl = temp.querySelector('a') || temp.closest('a');
						}
					}

					// 3. Letzter Fallback: Das erste <a> Element im Container nehmen
					if (!linkEl) linkEl = item.querySelector('a');
					if (!linkEl) continue;

					// 4. Sicherheits-Check: Hat das gefundene Element WIRKLICH ein href-Attribut?
					if (!linkEl.href && !linkEl.getAttribute('href')) {
						let fallback = item.querySelector('a[href]');
						if (fallback) linkEl = fallback;
						else continue; // Wenn wirklich kein Link existiert, überspringen
}
                    
                    const url = decodeUrl(linkEl.href || linkEl.getAttribute('href'), decodeMethod);
                    let title = titleEl ? titleEl.innerText.trim() : (linkEl.innerText.trim() || (type === "video" ? "Video Result" : (type === "image" ? "Image Result" : "Result")));
                    
                    let snippet = "";
                    if (rule.snippet && rule.snippet.selector) {
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
                    }

					let imageUrl = "";
                    let finalUrl = url; 

                    try { finalUrl = new URL(finalUrl, window.location.origin).toString(); } catch(e) {}
                    
                    // --- NEUER AD-FILTER (Doppelter Boden) ---
                    // Wenn der originale Link ein Google Ad-Link ist, zwingen wir den Typ auf "ad".
                    // So landet er nie in "organic", selbst wenn YouTube neue Container-Namen erfindet.
                    if (finalUrl.includes('googleadservices.com') || finalUrl.includes('doubleclick.net')) {
                        type = "ad";
                    }
                    // -----------------------------------------

					if (finalUrl.includes('googleadservices.com') || finalUrl.includes('doubleclick.net')) {
						try {
							const u = new URL(finalUrl);
							// Wenn es ein YouTube-Video ist:
							if (u.searchParams.has('video_id')) {
								finalUrl = 'https://www.youtube.com/watch?v=' + u.searchParams.get('video_id');
							} 
							// Für generelle Google Ads (greift auch bei der google.json):
							else if (u.searchParams.has('adurl')) {
								finalUrl = u.searchParams.get('adurl');
							}
						} catch(e) {}
					}

                    const bingLink = item.querySelector('a[m]') || (item.hasAttribute('m') ? item : null);
                    if (bingLink) {
                        const bingDataStr = bingLink.getAttribute('m');
                        if (bingDataStr) {
                            try {
                                const bingData = JSON.parse(bingDataStr);
                                if (bingData.murl) imageUrl = bingData.murl; 
                                if (bingData.purl) finalUrl = bingData.purl; 
                            } catch(e) {}
                        }
                    }

                    if (!imageUrl || finalUrl === url) {
                        const paramLink = item.querySelector('a[href*="imgres?"], a[href*="mediaurl="]');
                        if (paramLink) {
                            try {
                                const urlObj = new URL(paramLink.href, window.location.origin);
                                const highResUrl = urlObj.searchParams.get('imgurl') || urlObj.searchParams.get('mediaurl');
                                if (highResUrl) imageUrl = highResUrl;
                                
                                const hostPageUrl = urlObj.searchParams.get('imgrefurl');
                                if (hostPageUrl) finalUrl = hostPageUrl;
                            } catch(e) {}
                        }
                    }

                    if (!imageUrl && rule.image) {
                        const imgEl = item.querySelector(rule.image);
                        if (imgEl) imageUrl = imgEl.src || imgEl.getAttribute('data-src') || imgEl.getAttribute('src') || "";
                    }

					if (!finalUrl || finalUrl === "N/A") continue;
                    
                    // --- VERBESSERTER FILTER ---
                    // Schließt Shorts nur aus, wenn die URL auch wirklich zu YouTube gehört
                    // (Verhindert false positives bei Suchmaschinen, z.B. bei der Suche nach Kleidung)
                    if (finalUrl.includes('/shorts/') && finalUrl.includes('youtube.')) {
                        continue;
                    }
                    // ---------------------------

                    const engineHost = config.request.baseUrl.split('/')[2];
                    
                    // Exclude internal routing links except image results
                    if (finalUrl.includes(engineHost) && !finalUrl.includes('/ck/a') && !finalUrl.includes('imgres') && !finalUrl.includes('watch?v=')) {
                        // We allow watch?v= because YouTube scraper needs it
                        if(engineHost !== "www.youtube.com") continue;
                    }

                    if (type === "ad") {
                        result.ads.push({ rank: result.ads.length + 1, title: title, url: finalUrl, snippet: snippet, imageUrl: imageUrl });
                    } else if (type === "video" && isValidSourceUrl(finalUrl, config)) {
                        const channelEl = rule.channel ? item.querySelector(rule.channel) : null;
                        const durationEl = rule.duration ? item.querySelector(rule.duration) : null;
                        const dateEl = rule.date ? item.querySelector(rule.date) : null;

                        let channelText = channelEl ? channelEl.innerText.trim() : "";
                        let durationText = durationEl ? durationEl.innerText.trim() : "";
                        let dateText = dateEl ? dateEl.innerText.trim() : "";

                        let extraInfo = [channelText, durationText, dateText].filter(Boolean).join(" | ");

                        result.videos.push({ 
                            rank: rankOffset + result.videos.length + 1, 
                            title: title, 
                            url: finalUrl, 
                            snippet: extraInfo || snippet, 
                            imageUrl: imageUrl 
                        });
                    } else if (type === "image" && isValidSourceUrl(finalUrl, config)) {
                        result.images.push({ rank: rankOffset + result.images.length + 1, title: title, url: finalUrl, snippet: snippet, imageUrl: imageUrl });
                    } else if (type === "organic" && isValidSourceUrl(finalUrl, config)) {
                        result.organic.push({ rank: rankOffset + result.organic.length + 1, title: title, url: finalUrl, snippet: snippet, imageUrl: imageUrl });
                    }
                }
            }
        }
        
        sessionStorage.setItem("rat_organic_count", (rankOffset + result.organic.length + result.images.length + result.videos.length).toString());
        return result;
    }

    // --- NAVIGATION ---
    async function navigateToNext(config) {
        if (config.selectors.pagination && config.selectors.pagination.type === "infinite_scroll") {
            const getDocHeight = () => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
            window.scrollTo(0, getDocHeight());
            
            document.querySelectorAll('#page-manager, ytd-app, #content, ytd-search').forEach(el => {
                if (el.scrollHeight > el.clientHeight) {
                    try { el.scrollTo(0, el.scrollHeight); } catch(e) {}
                }
            });

            await wait(2500); 
            
            if (config.selectors.pagination.nextButton) {
                let btn = document.querySelector(config.selectors.pagination.nextButton);
                // offsetParent check entfernt, da Web Components wie ytd-continuation-item oft null zurückgeben
                if (btn) {
                    try {
                        btn.scrollIntoView({ block: "end", behavior: "smooth" });
                        await wait(800);
                        btn.click();
                    } catch(e){}
                }
            }
            
            await wait(2000); 
            return { success: true };
        }

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