const fc = require("fast-check");
const { generateUule, buildSearchUrl, getRandomDelay, parseProxyLine,
        parseProxyList, buildProxyConfig, selectRandomProxy, getRetryDelay,
        buildTaskMatrix, isSessionPaused, applyRetry, applyCancelTask,
        applyTaskReset, cancelTasksForConfig, buildSessionStatusPayload } = require('./src/utils');
const { openDB, saveSession, getSession, getAllSessions, deleteSession,
        savePageContent, getPageContent } = require('./src/db');
const { IDBFactory } = require('fake-indexeddb');

// ─────────────────────────────────────────────
// Helpers / Fixtures
// ─────────────────────────────────────────────

function makeEngine(overrides = {}) {
    return {
        engine: { id: "google", name: "Google" },
        request: {
            baseUrl: "https://www.google.{domain}/search",
            params: {
                query: "q",
                country: "gl",
                language: "hl",
                location: "uule",
            },
            features: {},
            ...overrides.request,
        },
        ...overrides,
    };
}

function makeTaskConfig(overrides = {}) {
    return {
        domain: "com",
        countryCode: "US",
        langCode: "en",
        engineId: "google",
        engineName: "Google",
        ...overrides,
    };
}

// ─────────────────────────────────────────────
// buildSearchUrl — fixed tests
// ─────────────────────────────────────────────

describe("buildSearchUrl() — fixed inputs", () => {
    test("builds a basic URL correctly", () => {
        const url = buildSearchUrl("seo tools", makeTaskConfig(), makeEngine());
        const parsed = new URL(url);
        expect(parsed.hostname).toBe("www.google.com");
        expect(parsed.searchParams.get("q")).toBe("seo tools");
        expect(parsed.searchParams.get("gl")).toBe("US");
        expect(parsed.searchParams.get("hl")).toBe("en");
    });

    test("replaces {domain} placeholder in baseUrl", () => {
        const url = buildSearchUrl("test", makeTaskConfig({ domain: "de" }), makeEngine());
        expect(url).toContain("google.de");
    });

    test("encodes special characters in the search term", () => {
        const url = buildSearchUrl("C++ tutorial", makeTaskConfig(), makeEngine());
        expect(new URL(url).searchParams.get("q")).toBe("C++ tutorial");
    });

    test("encodes quoted phrases in the search term", () => {
        const url = buildSearchUrl('"exact phrase"', makeTaskConfig(), makeEngine());
        expect(new URL(url).searchParams.get("q")).toBe('"exact phrase"');
    });

    test("omits country param if countryCode is missing", () => {
        const url = buildSearchUrl("test", makeTaskConfig({ countryCode: undefined }), makeEngine());
        expect(new URL(url).searchParams.has("gl")).toBe(false);
    });

    test("omits language param if langCode is missing", () => {
        const url = buildSearchUrl("test", makeTaskConfig({ langCode: undefined }), makeEngine());
        expect(new URL(url).searchParams.has("hl")).toBe(false);
    });

    test("appends UULE param when requiresUuleEncoding is true and location is set", () => {
        const engine = makeEngine({
            request: {
                baseUrl: "https://www.google.{domain}/search",
                params: { query: "q", country: "gl", language: "hl", location: "uule" },
                features: { requiresUuleEncoding: true },
            },
        });
        const url = buildSearchUrl("test", makeTaskConfig({ location: "Berlin, Germany" }), engine);
        const parsed = new URL(url);
        expect(parsed.searchParams.has("uule")).toBe(true);
        expect(parsed.searchParams.get("uule")).toMatch(/^w\+CAIQICI/);
    });

    test("does NOT append UULE param when requiresUuleEncoding is false", () => {
        const engine = makeEngine({
            request: {
                baseUrl: "https://www.google.{domain}/search",
                params: { query: "q", country: "gl", language: "hl", location: "uule" },
                features: { requiresUuleEncoding: false },
            },
        });
        const url = buildSearchUrl("test", makeTaskConfig({ location: "Berlin" }), engine);
        expect(new URL(url).searchParams.has("uule")).toBe(false);
    });

    test("does NOT append UULE param when location is not set", () => {
        const engine = makeEngine({
            request: {
                baseUrl: "https://www.google.{domain}/search",
                params: { query: "q", country: "gl", language: "hl", location: "uule" },
                features: { requiresUuleEncoding: true },
            },
        });
        const url = buildSearchUrl("test", makeTaskConfig(), engine);
        expect(new URL(url).searchParams.has("uule")).toBe(false);
    });

    test("handles unicode / emoji in search term", () => {
        const url = buildSearchUrl("café ☕", makeTaskConfig(), makeEngine());
        expect(new URL(url).searchParams.get("q")).toBe("café ☕");
    });

    test("handles script injection attempt in search term", () => {
        const url = buildSearchUrl("<script>alert('xss')</script>", makeTaskConfig(), makeEngine());
        expect(new URL(url).searchParams.get("q")).toBe("<script>alert('xss')</script>");
    });

    test("handles SQL injection attempt in search term", () => {
        const url = buildSearchUrl("'; DROP TABLE results;--", makeTaskConfig(), makeEngine());
        expect(new URL(url).searchParams.get("q")).toBe("'; DROP TABLE results;--");
    });

    test("handles very long search term (500 chars)", () => {
        const long = "a".repeat(500);
        const url = buildSearchUrl(long, makeTaskConfig(), makeEngine());
        expect(new URL(url).searchParams.get("q")).toBe(long);
    });

    test("handles search term that is only whitespace", () => {
        expect(() => buildSearchUrl("   ", makeTaskConfig(), makeEngine())).not.toThrow();
    });

    test("handles empty string as search term", () => {
        expect(() => buildSearchUrl("", makeTaskConfig(), makeEngine())).not.toThrow();
    });
});

// ─────────────────────────────────────────────
// buildSearchUrl — property-based tests
// ─────────────────────────────────────────────

describe("buildSearchUrl() — property-based (random inputs)", () => {
    test("never throws for any string as search term", () => {
        fc.assert(
            fc.property(fc.string(), (term) => {
                expect(() => buildSearchUrl(term, makeTaskConfig(), makeEngine())).not.toThrow();
            }),
            { numRuns: 500 }
        );
    });

    test("always produces a valid URL for any search term", () => {
        fc.assert(
            fc.property(fc.string(), (term) => {
                const url = buildSearchUrl(term, makeTaskConfig(), makeEngine());
                expect(() => new URL(url)).not.toThrow();
            }),
            { numRuns: 500 }
        );
    });

    test("always preserves the search term exactly in the query param", () => {
        fc.assert(
            fc.property(fc.string(), (term) => {
                const url = buildSearchUrl(term, makeTaskConfig(), makeEngine());
                expect(new URL(url).searchParams.get("q")).toBe(term);
            }),
            { numRuns: 500 }
        );
    });

    test("never throws for any countryCode / langCode combination", () => {
        fc.assert(
            fc.property(fc.string(), fc.string(), (countryCode, langCode) => {
                expect(() =>
                    buildSearchUrl("test", makeTaskConfig({ countryCode, langCode }), makeEngine())
                ).not.toThrow();
            }),
            { numRuns: 300 }
        );
    });

    test("never throws for any valid domain", () => {
        fc.assert(
            fc.property(fc.stringMatching(/^[a-z]{2,10}$/), (domain) => {
                expect(() =>
                    buildSearchUrl("test", makeTaskConfig({ domain }), makeEngine())
                ).not.toThrow();
            }),
            { numRuns: 200 }
        );
    });
});

// ─────────────────────────────────────────────
// generateUule — fixed tests
// ─────────────────────────────────────────────

describe("generateUule() — fixed inputs", () => {
    test("always starts with the expected prefix", () => {
        expect(generateUule("Berlin")).toMatch(/^w\+CAIQICI/);
    });

    test("encodes the location string via btoa", () => {
        const loc = "New York, USA";
        expect(generateUule(loc)).toContain(btoa(loc));
    });

    test("uses correct secret character for given location length", () => {
        const secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
        const loc = "Tokyo"; // length 5 → secret[5] = "F"
        expect(generateUule(loc)).toContain(`w+CAIQICI${secret[5 % 65]}`);
    });

    test("handles empty string without throwing", () => {
        expect(() => generateUule("")).not.toThrow();
    });

    test("handles a very long location name (200 chars)", () => {
        const long = "A".repeat(200);
        expect(() => generateUule(long)).not.toThrow();
        expect(generateUule(long)).toMatch(/^w\+CAIQICI/);
    });

    test("handles special characters and umlauts", () => {
        expect(() => generateUule("München, Schwabing-Freimann")).not.toThrow();
    });

    test("two different locations produce different results", () => {
        expect(generateUule("London")).not.toBe(generateUule("Paris"));
    });
});

// ─────────────────────────────────────────────
// generateUule — property-based tests
// ─────────────────────────────────────────────

describe("generateUule() — property-based (random inputs)", () => {
    test("never throws for any string input", () => {
        fc.assert(
            fc.property(fc.string(), (loc) => {
                expect(() => generateUule(loc)).not.toThrow();
            }),
            { numRuns: 500 }
        );
    });

    test("always starts with expected prefix for any input", () => {
        fc.assert(
            fc.property(fc.string(), (loc) => {
                expect(generateUule(loc)).toMatch(/^w\+CAIQICI/);
            }),
            { numRuns: 500 }
        );
    });

    test("two different non-empty strings always produce different results", () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 1 }),
                fc.string({ minLength: 1 }),
                (a, b) => {
                    fc.pre(a !== b);
                    expect(generateUule(a)).not.toBe(generateUule(b));
                }
            ),
            { numRuns: 300 }
        );
    });
});

// ─────────────────────────────────────────────
// getRandomDelay — fixed tests
// ─────────────────────────────────────────────

describe("getRandomDelay() — fixed inputs", () => {
    test("returns a number", () => {
        expect(typeof getRandomDelay(1000, 5000)).toBe("number");
    });

    test("result is always within [min, max]", () => {
        for (let i = 0; i < 200; i++) {
            const val = getRandomDelay(1000, 5000);
            expect(val).toBeGreaterThanOrEqual(1000);
            expect(val).toBeLessThanOrEqual(5000);
        }
    });

    test("returns exact value when min === max", () => {
        expect(getRandomDelay(3000, 3000)).toBe(3000);
    });

    test("always returns an integer", () => {
        for (let i = 0; i < 50; i++) {
            expect(Number.isInteger(getRandomDelay(0, 10000))).toBe(true);
        }
    });

    test("works with zero as min", () => {
        const val = getRandomDelay(0, 100);
        expect(val).toBeGreaterThanOrEqual(0);
        expect(val).toBeLessThanOrEqual(100);
    });
});

// ─────────────────────────────────────────────
// getRandomDelay — property-based tests
// ─────────────────────────────────────────────

describe("getRandomDelay() — property-based (random inputs)", () => {
    test("always returns a value within [min, max] for any valid range", () => {
        fc.assert(
            fc.property(
                fc.integer({ min: 0, max: 50000 }),
                fc.integer({ min: 0, max: 50000 }),
                (a, b) => {
                    const min = Math.min(a, b);
                    const max = Math.max(a, b);
                    const val = getRandomDelay(min, max);
                    expect(val).toBeGreaterThanOrEqual(min);
                    expect(val).toBeLessThanOrEqual(max);
                }
            ),
            { numRuns: 500 }
        );
    });

    test("always returns an integer for any valid range", () => {
        fc.assert(
            fc.property(
                fc.integer({ min: 0, max: 50000 }),
                fc.integer({ min: 0, max: 50000 }),
                (a, b) => {
                    const val = getRandomDelay(Math.min(a, b), Math.max(a, b));
                    expect(Number.isInteger(val)).toBe(true);
                }
            ),
            { numRuns: 500 }
        );
    });
});

// ─────────────────────────────────────────────
// parseProxyLine — fixed tests
// ─────────────────────────────────────────────

describe("parseProxyLine() — fixed inputs", () => {
    test("parses a valid proxy line correctly", () => {
        expect(parseProxyLine("192.168.1.1:8080:user:pass")).toEqual({
            ip: "192.168.1.1", port: 8080, user: "user", pass: "pass"
        });
    });

    test("returns null for missing field (only 3 parts)", () => {
        expect(parseProxyLine("192.168.1.1:8080:user")).toBeNull();
    });

    test("returns null for too many parts", () => {
        expect(parseProxyLine("192.168.1.1:8080:user:pass:extra")).toBeNull();
    });

    test("returns null for empty string", () => {
        expect(parseProxyLine("")).toBeNull();
    });

    test("returns null for non-numeric port", () => {
        expect(parseProxyLine("192.168.1.1:abc:user:pass")).toBeNull();
    });

    test("trims whitespace from the line", () => {
        const result = parseProxyLine("  10.0.0.1:3128:admin:secret  ");
        expect(result).not.toBeNull();
        expect(result.ip).toBe("10.0.0.1");
    });

    test("parses port as a number, not a string", () => {
        expect(typeof parseProxyLine("10.0.0.1:3128:user:pass").port).toBe("number");
    });

    test("handles special characters in username and password", () => {
        const result = parseProxyLine("10.0.0.1:3128:us€r:p@$$w0rd!");
        expect(result).not.toBeNull();
        expect(result.user).toBe("us€r");
        expect(result.pass).toBe("p@$$w0rd!");
    });
});

// ─────────────────────────────────────────────
// parseProxyLine — property-based tests
// ─────────────────────────────────────────────

describe("parseProxyLine() — property-based (random inputs)", () => {
    test("never throws for any string input", () => {
        fc.assert(
            fc.property(fc.string(), (line) => {
                expect(() => parseProxyLine(line)).not.toThrow();
            }),
            { numRuns: 500 }
        );
    });

    test("always returns null or a valid object — never something in between", () => {
        fc.assert(
            fc.property(fc.string(), (line) => {
                const result = parseProxyLine(line);
                const isNull = result === null;
                const isValid = typeof result === "object" && result !== null &&
                    "ip" in result && "port" in result && "user" in result && "pass" in result;
                expect(isNull || isValid).toBe(true);
            }),
            { numRuns: 500 }
        );
    });

    test("always returns a numeric port when result is not null", () => {
        fc.assert(
            fc.property(fc.string(), (line) => {
                const result = parseProxyLine(line);
                if (result !== null) {
                    expect(typeof result.port).toBe("number");
                    expect(isNaN(result.port)).toBe(false);
                }
            }),
            { numRuns: 500 }
        );
    });

    test("valid IP:port:user:pass format always parses successfully", () => {
        fc.assert(
            fc.property(
                fc.ipV4(),
                fc.integer({ min: 1, max: 65535 }),
                fc.stringMatching(/^[a-zA-Z0-9]+$/),
                fc.stringMatching(/^[a-zA-Z0-9]+$/),
                (ip, port, user, pass) => {
                    const result = parseProxyLine(`${ip}:${port}:${user}:${pass}`);
                    expect(result).not.toBeNull();
                    expect(result.ip).toBe(ip);
                    expect(result.port).toBe(port);
                }
            ),
            { numRuns: 300 }
        );
    });
});

// ─────────────────────────────────────────────
// Proxy-Rotation — parseProxyList
// ─────────────────────────────────────────────

describe("parseProxyList() — textarea string → filtered array", () => {
    test("splits a multi-line string into individual entries", () => {
        const str = "1.2.3.4:8080:user:pass\n5.6.7.8:3128:admin:secret";
        expect(parseProxyList(str)).toHaveLength(2);
    });

    test("trims whitespace from each line", () => {
        const str = "  1.2.3.4:8080:user:pass  \n  5.6.7.8:3128:admin:secret  ";
        const list = parseProxyList(str);
        expect(list[0]).toBe("1.2.3.4:8080:user:pass");
    });

    test("filters out lines shorter than 6 characters", () => {
        const str = "short\n1.2.3.4:8080:user:pass";
        expect(parseProxyList(str)).toHaveLength(1);
    });

    test("filters out blank lines", () => {
        const str = "1.2.3.4:8080:u:p\n\n\n5.6.7.8:3128:a:b";
        expect(parseProxyList(str)).toHaveLength(2);
    });

    test("returns empty array for empty string", () => {
        expect(parseProxyList("")).toHaveLength(0);
    });

    test("returns empty array for null/undefined", () => {
        expect(parseProxyList(null)).toHaveLength(0);
        expect(parseProxyList(undefined)).toHaveLength(0);
    });

    test("single valid line produces a one-element array", () => {
        expect(parseProxyList("1.2.3.4:8080:user:pass")).toHaveLength(1);
    });
});

// ─────────────────────────────────────────────
// Proxy-Rotation — buildProxyConfig
// ─────────────────────────────────────────────

describe("buildProxyConfig() — Chrome proxy settings object", () => {
    test("sets mode to fixed_servers", () => {
        expect(buildProxyConfig("1.2.3.4", 8080).mode).toBe("fixed_servers");
    });

    test("sets scheme to http", () => {
        expect(buildProxyConfig("1.2.3.4", 8080).rules.singleProxy.scheme).toBe("http");
    });

    test("sets host correctly", () => {
        expect(buildProxyConfig("10.0.0.1", 3128).rules.singleProxy.host).toBe("10.0.0.1");
    });

    test("parses port string to number", () => {
        const cfg = buildProxyConfig("1.2.3.4", "9090");
        expect(typeof cfg.rules.singleProxy.port).toBe("number");
        expect(cfg.rules.singleProxy.port).toBe(9090);
    });

    test("bypassList always contains localhost and 127.0.0.1", () => {
        const { bypassList } = buildProxyConfig("1.2.3.4", 8080).rules;
        expect(bypassList).toContain("localhost");
        expect(bypassList).toContain("127.0.0.1");
    });
});

// ─────────────────────────────────────────────
// Proxy-Rotation — selectRandomProxy
// ─────────────────────────────────────────────

describe("selectRandomProxy() — random selection", () => {
    test("returns null for empty list", () => {
        expect(selectRandomProxy([])).toBeNull();
    });

    test("returns null for null/undefined", () => {
        expect(selectRandomProxy(null)).toBeNull();
        expect(selectRandomProxy(undefined)).toBeNull();
    });

    test("always returns an element that exists in the list", () => {
        const list = ["a:1:u:p", "b:2:u:p", "c:3:u:p"];
        for (let i = 0; i < 50; i++) {
            expect(list).toContain(selectRandomProxy(list));
        }
    });

    test("returns the only element for a single-entry list", () => {
        expect(selectRandomProxy(["1.2.3.4:8080:u:p"])).toBe("1.2.3.4:8080:u:p");
    });

    test("eventually selects every entry in a small list (distribution check)", () => {
        const list = ["a", "b", "c"];
        const seen = new Set();
        for (let i = 0; i < 300; i++) seen.add(selectRandomProxy(list));
        expect(seen.size).toBe(3);
    });

    test("property: never returns a value outside the list", () => {
        fc.assert(
            fc.property(
                fc.array(fc.string({ minLength: 6 }), { minLength: 1, maxLength: 20 }),
                (list) => {
                    expect(list).toContain(selectRandomProxy(list));
                }
            ),
            { numRuns: 300 }
        );
    });
});

// ─────────────────────────────────────────────
// Proxy-Rotation — getRetryDelay (CAPTCHA back-off)
// ─────────────────────────────────────────────

describe("getRetryDelay() — CAPTCHA back-off schedule", () => {
    const RETRY_DELAYS = [5, 15, 30, 60];

    test("first retry uses first delay", () => {
        expect(getRetryDelay(0, RETRY_DELAYS)).toBe(5);
    });

    test("second retry uses second delay", () => {
        expect(getRetryDelay(1, RETRY_DELAYS)).toBe(15);
    });

    test("clamps to last delay when retryCount exceeds list length", () => {
        expect(getRetryDelay(99, RETRY_DELAYS)).toBe(60);
    });

    test("last valid index returns last delay", () => {
        expect(getRetryDelay(3, RETRY_DELAYS)).toBe(60);
    });

    test("delay always increases or stays equal (monotone schedule)", () => {
        for (let i = 0; i < RETRY_DELAYS.length - 1; i++) {
            expect(getRetryDelay(i, RETRY_DELAYS)).toBeLessThanOrEqual(getRetryDelay(i + 1, RETRY_DELAYS));
        }
    });
});

// ─────────────────────────────────────────────
// IndexedDB-Persistenz — Session CRUD
// ─────────────────────────────────────────────

describe("IndexedDB — Session-Persistenz", () => {
    let db;

    beforeEach(async () => {
        db = await openDB(new IDBFactory());
    });

    function makeSession(id = "sess_1", overrides = {}) {
        return { id, name: "Test", status: "OPEN", tasks: [], currentIndex: 0,
                 globalCount: 10, delays: { min: 3000, max: 8000 },
                 settings: { saveSerp: false, useProxies: false, proxyList: [] },
                 originalConfigs: [], originalQueries: [], ...overrides };
    }

    test("saved session can be retrieved by id", async () => {
        const session = makeSession("sess_abc");
        await saveSession(db, session);
        const result = await getSession(db, "sess_abc");
        expect(result).not.toBeUndefined();
        expect(result.id).toBe("sess_abc");
    });

    test("retrieved session matches saved data exactly", async () => {
        const session = makeSession("sess_x", { name: "My Study", globalCount: 25 });
        await saveSession(db, session);
        const result = await getSession(db, "sess_x");
        expect(result.name).toBe("My Study");
        expect(result.globalCount).toBe(25);
    });

    test("missing session returns undefined", async () => {
        const result = await getSession(db, "does_not_exist");
        expect(result).toBeUndefined();
    });

    test("put overwrites an existing session (update)", async () => {
        const session = makeSession("sess_1", { status: "OPEN" });
        await saveSession(db, session);
        await saveSession(db, { ...session, status: "RUNNING" });
        const result = await getSession(db, "sess_1");
        expect(result.status).toBe("RUNNING");
    });

    test("getAllSessions returns all stored sessions", async () => {
        await saveSession(db, makeSession("sess_1"));
        await saveSession(db, makeSession("sess_2"));
        const all = await getAllSessions(db);
        expect(all).toHaveLength(2);
    });

    test("getAllSessions returns empty array when store is empty", async () => {
        const all = await getAllSessions(db);
        expect(all).toEqual([]);
    });

    test("deleted session is no longer retrievable", async () => {
        await saveSession(db, makeSession("sess_del"));
        await deleteSession(db, "sess_del");
        const result = await getSession(db, "sess_del");
        expect(result).toBeUndefined();
    });

    test("deleting a non-existent session does not throw", async () => {
        await expect(deleteSession(db, "ghost")).resolves.not.toThrow();
    });

    test("status field is persisted correctly", async () => {
        for (const status of ["OPEN", "RUNNING", "PAUSED", "DONE", "PAUSED_CAPTCHA"]) {
            const s = makeSession(`sess_${status}`, { status });
            await saveSession(db, s);
            const r = await getSession(db, `sess_${status}`);
            expect(r.status).toBe(status);
        }
    });

    test("tasks array with entries round-trips correctly", async () => {
        const tasks = [
            { term: "AI tools", config: { engineId: "google" }, status: "DONE", pages: [], totalOrganic: 5, retryCount: 0 },
            { term: "SEO tips", config: { engineId: "bing"   }, status: "OPEN", pages: [], totalOrganic: 0, retryCount: 0 },
        ];
        await saveSession(db, makeSession("sess_tasks", { tasks }));
        const result = await getSession(db, "sess_tasks");
        expect(result.tasks).toHaveLength(2);
        expect(result.tasks[0].term).toBe("AI tools");
        expect(result.tasks[1].status).toBe("OPEN");
    });
});

// ─────────────────────────────────────────────
// IndexedDB-Persistenz — Page Content (STORE_RESULTS)
// ─────────────────────────────────────────────

describe("IndexedDB — Page-Content-Persistenz", () => {
    let db;

    beforeEach(async () => {
        db = await openDB(new IDBFactory());
    });

    test("saved page content can be retrieved by composite key", async () => {
        await savePageContent(db, "sess_1", 0, 1, { html: "<p>test</p>", screenshot: null });
        const result = await getPageContent(db, "sess_1", 0, 1);
        expect(result).not.toBeUndefined();
        expect(result.html).toBe("<p>test</p>");
    });

    test("different page numbers produce different entries", async () => {
        await savePageContent(db, "sess_1", 0, 1, { html: "page1" });
        await savePageContent(db, "sess_1", 0, 2, { html: "page2" });
        const p1 = await getPageContent(db, "sess_1", 0, 1);
        const p2 = await getPageContent(db, "sess_1", 0, 2);
        expect(p1.html).toBe("page1");
        expect(p2.html).toBe("page2");
    });

    test("different task indices produce different entries", async () => {
        await savePageContent(db, "sess_1", 0, 1, { html: "task0" });
        await savePageContent(db, "sess_1", 1, 1, { html: "task1" });
        expect((await getPageContent(db, "sess_1", 0, 1)).html).toBe("task0");
        expect((await getPageContent(db, "sess_1", 1, 1)).html).toBe("task1");
    });

    test("missing key returns undefined", async () => {
        const result = await getPageContent(db, "sess_x", 99, 99);
        expect(result).toBeUndefined();
    });

    test("overwriting same key updates the content", async () => {
        await savePageContent(db, "sess_1", 0, 1, { html: "old" });
        await savePageContent(db, "sess_1", 0, 1, { html: "new" });
        const result = await getPageContent(db, "sess_1", 0, 1);
        expect(result.html).toBe("new");
    });

    test("screenshot field is stored alongside html", async () => {
        const screenshot = "data:image/jpeg;base64,abc123";
        await savePageContent(db, "sess_1", 0, 1, { html: null, screenshot });
        const result = await getPageContent(db, "sess_1", 0, 1);
        expect(result.screenshot).toBe(screenshot);
    });
});

// ─────────────────────────────────────────────
// buildTaskMatrix — queries × configs cross-product
// ─────────────────────────────────────────────

describe("buildTaskMatrix() — task generation", () => {
    const q2 = ["climate change", "AI tools"];
    const c2 = [
        { engineId: "google", engineName: "Google", countryCode: "US", langCode: "en", domain: "com" },
        { engineId: "bing",   engineName: "Bing",   countryCode: "DE", langCode: "de", domain: "de"  },
    ];

    test("2 queries × 2 configs produces 4 tasks", () => {
        expect(buildTaskMatrix(q2, c2)).toHaveLength(4);
    });

    test("every task has status OPEN", () => {
        buildTaskMatrix(q2, c2).forEach(t => expect(t.status).toBe("OPEN"));
    });

    test("every task starts with retryCount 0", () => {
        buildTaskMatrix(q2, c2).forEach(t => expect(t.retryCount).toBe(0));
    });

    test("every task starts with empty pages array", () => {
        buildTaskMatrix(q2, c2).forEach(t => expect(t.pages).toEqual([]));
    });

    test("every task starts with totalOrganic 0", () => {
        buildTaskMatrix(q2, c2).forEach(t => expect(t.totalOrganic).toBe(0));
    });

    test("each query appears in exactly (configs.length) tasks", () => {
        const tasks = buildTaskMatrix(q2, c2);
        q2.forEach(q => {
            expect(tasks.filter(t => t.term === q)).toHaveLength(c2.length);
        });
    });

    test("each config appears in exactly (queries.length) tasks", () => {
        const tasks = buildTaskMatrix(q2, c2);
        c2.forEach(conf => {
            expect(tasks.filter(t => t.config.engineId === conf.engineId)).toHaveLength(q2.length);
        });
    });

    test("0 queries → 0 tasks", () => {
        expect(buildTaskMatrix([], c2)).toHaveLength(0);
    });

    test("0 configs → 0 tasks", () => {
        expect(buildTaskMatrix(q2, [])).toHaveLength(0);
    });

    test("1 query × 1 config → 1 task with correct term and config", () => {
        const tasks = buildTaskMatrix(["seo"], [c2[0]]);
        expect(tasks).toHaveLength(1);
        expect(tasks[0].term).toBe("seo");
        expect(tasks[0].config.engineId).toBe("google");
    });

    test("property: task count always equals queries.length × configs.length", () => {
        fc.assert(
            fc.property(
                fc.array(fc.string({ minLength: 1 }), { minLength: 0, maxLength: 10 }),
                fc.array(fc.record({ engineId: fc.string(), engineName: fc.string(),
                                     countryCode: fc.string(), langCode: fc.string(), domain: fc.string() }),
                         { minLength: 0, maxLength: 5 }),
                (queries, configs) => {
                    expect(buildTaskMatrix(queries, configs)).toHaveLength(queries.length * configs.length);
                }
            ),
            { numRuns: 300 }
        );
    });

    test("property: every generated task always has status OPEN", () => {
        fc.assert(
            fc.property(
                fc.array(fc.string({ minLength: 1 }), { minLength: 1, maxLength: 5 }),
                fc.array(fc.record({ engineId: fc.string(), engineName: fc.string(),
                                     countryCode: fc.string(), langCode: fc.string(), domain: fc.string() }),
                         { minLength: 1, maxLength: 3 }),
                (queries, configs) => {
                    buildTaskMatrix(queries, configs).forEach(t => expect(t.status).toBe("OPEN"));
                }
            ),
            { numRuns: 200 }
        );
    });
});

// ─────────────────────────────────────────────
// isSessionPaused — session status guard
// ─────────────────────────────────────────────

describe("isSessionPaused() — session status guard", () => {
    test("null session → paused", () => {
        expect(isSessionPaused(null)).toBe(true);
    });

    test("undefined session → paused", () => {
        expect(isSessionPaused(undefined)).toBe(true);
    });

    test("status RUNNING → not paused", () => {
        expect(isSessionPaused({ status: "RUNNING" })).toBe(false);
    });

    test("status PAUSED → paused", () => {
        expect(isSessionPaused({ status: "PAUSED" })).toBe(true);
    });

    test("status OPEN → paused", () => {
        expect(isSessionPaused({ status: "OPEN" })).toBe(true);
    });

    test("status DONE → paused", () => {
        expect(isSessionPaused({ status: "DONE" })).toBe(true);
    });

    test("status PAUSED_CAPTCHA → paused", () => {
        expect(isSessionPaused({ status: "PAUSED_CAPTCHA" })).toBe(true);
    });

    test("property: only RUNNING ever returns false", () => {
        const NON_RUNNING = ["OPEN", "PAUSED", "DONE", "PAUSED_CAPTCHA", "FAILED", "CANCELLED"];
        NON_RUNNING.forEach(s => expect(isSessionPaused({ status: s })).toBe(true));
    });
});

// ─────────────────────────────────────────────
// applyRetry — retry logic & failure threshold
// ─────────────────────────────────────────────

describe("applyRetry() — retry count and failure threshold", () => {
    function makeTask(retryCount = 0) {
        return { term: "test", status: "OPEN", retryCount, pages: [], totalOrganic: 0 };
    }

    test("increments retryCount by 1", () => {
        const task = makeTask(0);
        applyRetry(task);
        expect(task.retryCount).toBe(1);
    });

    test("returns RETRY and keeps status OPEN on first attempt", () => {
        const task = makeTask(0);
        expect(applyRetry(task)).toBe("RETRY");
        expect(task.status).toBe("OPEN");
    });

    test("returns RETRY on second attempt", () => {
        const task = makeTask(1);
        expect(applyRetry(task)).toBe("RETRY");
    });

    test("returns RETRY on third attempt (retryCount becomes 3, not yet > 3)", () => {
        const task = makeTask(2);
        expect(applyRetry(task)).toBe("RETRY");
        expect(task.retryCount).toBe(3);
        expect(task.status).toBe("OPEN");
    });

    test("returns FAILED and sets status to FAILED on fourth attempt (retryCount > 3)", () => {
        const task = makeTask(3);
        expect(applyRetry(task)).toBe("FAILED");
        expect(task.status).toBe("FAILED");
        expect(task.retryCount).toBe(4);
    });

    test("returns FAILED for any retryCount already beyond maxRetries", () => {
        const task = makeTask(10);
        expect(applyRetry(task)).toBe("FAILED");
        expect(task.status).toBe("FAILED");
    });

    test("custom maxRetries=1: fails on second attempt", () => {
        const task = makeTask(1);
        expect(applyRetry(task, 1)).toBe("FAILED");
        expect(task.status).toBe("FAILED");
    });

    test("custom maxRetries=1: retries on first attempt", () => {
        const task = makeTask(0);
        expect(applyRetry(task, 1)).toBe("RETRY");
        expect(task.status).toBe("OPEN");
    });

    test("mutates the task object passed in", () => {
        const task = makeTask(0);
        const before = task.retryCount;
        applyRetry(task);
        expect(task.retryCount).toBe(before + 1);
    });

    test("property: result is always RETRY or FAILED, never anything else", () => {
        fc.assert(
            fc.property(fc.integer({ min: 0, max: 20 }), (startCount) => {
                const task = makeTask(startCount);
                const result = applyRetry(task);
                expect(["RETRY", "FAILED"]).toContain(result);
            }),
            { numRuns: 200 }
        );
    });

    test("property: FAILED result always coincides with status FAILED on the task", () => {
        fc.assert(
            fc.property(fc.integer({ min: 0, max: 20 }), (startCount) => {
                const task = makeTask(startCount);
                const result = applyRetry(task);
                if (result === "FAILED") expect(task.status).toBe("FAILED");
                if (result === "RETRY")  expect(task.status).toBe("OPEN");
            }),
            { numRuns: 200 }
        );
    });
});

// ─────────────────────────────────────────────
// applyCancelTask — cancel a non-DONE task
// ─────────────────────────────────────────────

describe("applyCancelTask() — task cancellation guard", () => {
    function makeTask(status) {
        return { term: "test", status, retryCount: 0 };
    }

    test("OPEN task is cancelled and returns true", () => {
        const task = makeTask("OPEN");
        expect(applyCancelTask(task)).toBe(true);
        expect(task.status).toBe("CANCELLED");
    });

    test("FAILED task is cancelled and returns true", () => {
        const task = makeTask("FAILED");
        expect(applyCancelTask(task)).toBe(true);
        expect(task.status).toBe("CANCELLED");
    });

    test("DONE task is NOT cancelled and returns false", () => {
        const task = makeTask("DONE");
        expect(applyCancelTask(task)).toBe(false);
        expect(task.status).toBe("DONE");
    });

    test("already CANCELLED task is set to CANCELLED and returns true", () => {
        const task = makeTask("CANCELLED");
        expect(applyCancelTask(task)).toBe(true);
        expect(task.status).toBe("CANCELLED");
    });

    test("DONE task status is never mutated", () => {
        const task = makeTask("DONE");
        applyCancelTask(task);
        expect(task.status).toBe("DONE");
    });
});

// ─────────────────────────────────────────────
// applyTaskReset — reset task to initial state
// ─────────────────────────────────────────────

describe("applyTaskReset() — task reset to OPEN", () => {
    function makeTask(overrides = {}) {
        return { term: "test", status: "FAILED", retryCount: 3,
                 pages: [{ pageNumber: 1 }], totalOrganic: 12, ...overrides };
    }

    test("sets status to OPEN", () => {
        expect(applyTaskReset(makeTask()).status).toBe("OPEN");
    });

    test("resets retryCount to 0", () => {
        expect(applyTaskReset(makeTask()).retryCount).toBe(0);
    });

    test("clears pages array", () => {
        expect(applyTaskReset(makeTask()).pages).toEqual([]);
    });

    test("resets totalOrganic to 0", () => {
        expect(applyTaskReset(makeTask()).totalOrganic).toBe(0);
    });

    test("returns the same task object (mutates in place)", () => {
        const task = makeTask();
        expect(applyTaskReset(task)).toBe(task);
    });

    test("preserves the term field", () => {
        const task = makeTask({ term: "my query" });
        applyTaskReset(task);
        expect(task.term).toBe("my query");
    });

    test("works regardless of prior status", () => {
        ["FAILED", "DONE", "CANCELLED", "PAUSED_CAPTCHA"].forEach(status => {
            const task = makeTask({ status });
            applyTaskReset(task);
            expect(task.status).toBe("OPEN");
        });
    });
});

// ─────────────────────────────────────────────
// cancelTasksForConfig — remove an engine config from a session
// ─────────────────────────────────────────────

describe("cancelTasksForConfig() — engine config removal", () => {
    const targetConf = { countryCode: "DE", langCode: "de", domain: "de" };
    const otherConf  = { countryCode: "US", langCode: "en", domain: "com" };

    function makeTask(conf, status) {
        return { term: "test", config: conf, status };
    }

    test("cancels OPEN tasks matching the config", () => {
        const tasks = [makeTask(targetConf, "OPEN")];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("CANCELLED");
    });

    test("cancels FAILED tasks matching the config", () => {
        const tasks = [makeTask(targetConf, "FAILED")];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("CANCELLED");
    });

    test("does NOT cancel DONE tasks even if config matches", () => {
        const tasks = [makeTask(targetConf, "DONE")];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("DONE");
    });

    test("does NOT cancel tasks with a different config", () => {
        const tasks = [makeTask(otherConf, "OPEN")];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("OPEN");
    });

    test("returns the correct cancelled count", () => {
        const tasks = [
            makeTask(targetConf, "OPEN"),
            makeTask(targetConf, "FAILED"),
            makeTask(targetConf, "DONE"),
            makeTask(otherConf,  "OPEN"),
        ];
        expect(cancelTasksForConfig(tasks, targetConf)).toBe(2);
    });

    test("returns 0 when no tasks match", () => {
        const tasks = [makeTask(otherConf, "OPEN"), makeTask(otherConf, "FAILED")];
        expect(cancelTasksForConfig(tasks, targetConf)).toBe(0);
    });

    test("returns 0 for an empty task list", () => {
        expect(cancelTasksForConfig([], targetConf)).toBe(0);
    });

    test("mixed tasks: only matching OPEN/FAILED are cancelled", () => {
        const tasks = [
            makeTask(targetConf, "OPEN"),
            makeTask(targetConf, "DONE"),
            makeTask(targetConf, "FAILED"),
            makeTask(otherConf,  "OPEN"),
        ];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("CANCELLED");
        expect(tasks[1].status).toBe("DONE");
        expect(tasks[2].status).toBe("CANCELLED");
        expect(tasks[3].status).toBe("OPEN");
    });

    test("matching is exact: different countryCode is not affected", () => {
        const almostTarget = { countryCode: "AT", langCode: "de", domain: "de" };
        const tasks = [makeTask(almostTarget, "OPEN")];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("OPEN");
    });

    test("matching is exact: different domain is not affected", () => {
        const almostTarget = { countryCode: "DE", langCode: "de", domain: "at" };
        const tasks = [makeTask(almostTarget, "OPEN")];
        cancelTasksForConfig(tasks, targetConf);
        expect(tasks[0].status).toBe("OPEN");
    });
});

// ─────────────────────────────────────────────
// buildSessionStatusPayload — broadcast payload shape
// ─────────────────────────────────────────────

describe("buildSessionStatusPayload() — status broadcast shape", () => {
    function makeTask(status, term = "query", engineName = "Google") {
        return { term, config: { engineName }, status, pages: [], totalOrganic: 0, retryCount: 0 };
    }

    function makeSession(overrides = {}) {
        return {
            id: "sess_1", name: "My Study", status: "RUNNING",
            tasks: [], currentIndex: 0,
            globalCount: 50,
            delays: { min: 3000, max: 8000 },
            settings: { saveSerp: false, useProxies: false },
            originalConfigs: [],
            originalQueries: [],
            ...overrides,
        };
    }

    test("payload contains all required keys", () => {
        const payload = buildSessionStatusPayload(makeSession(), []);
        const keys = ["sessionId", "name", "status", "progress", "currentQuery",
                      "logs", "delays", "originalConfigs", "originalQueries", "settings", "globalCount"];
        keys.forEach(k => expect(payload).toHaveProperty(k));
    });

    test("sessionId matches session.id", () => {
        expect(buildSessionStatusPayload(makeSession({ id: "sess_abc" }), []).sessionId).toBe("sess_abc");
    });

    test("progress.done counts DONE tasks correctly", () => {
        const tasks = [makeTask("DONE"), makeTask("DONE"), makeTask("OPEN"), makeTask("FAILED")];
        const { progress } = buildSessionStatusPayload(makeSession({ tasks }), []);
        expect(progress.done).toBe(2);
        expect(progress.total).toBe(4);
    });

    test("progress.total is the full task count regardless of status", () => {
        const tasks = [makeTask("OPEN"), makeTask("CANCELLED"), makeTask("RUNNING")];
        expect(buildSessionStatusPayload(makeSession({ tasks }), []).progress.total).toBe(3);
    });

    test("progress.done is 0 when no tasks are DONE", () => {
        const tasks = [makeTask("OPEN"), makeTask("FAILED")];
        expect(buildSessionStatusPayload(makeSession({ tasks }), []).progress.done).toBe(0);
    });

    test("currentQuery shows 'term (engineName)' for the current task", () => {
        const tasks = [makeTask("OPEN", "climate change", "Bing")];
        const payload = buildSessionStatusPayload(makeSession({ tasks, currentIndex: 0 }), []);
        expect(payload.currentQuery).toBe("climate change (Bing)");
    });

    test("currentQuery is 'Done' when currentIndex points to undefined", () => {
        const session = makeSession({ tasks: [], currentIndex: 0 });
        expect(buildSessionStatusPayload(session, []).currentQuery).toBe("Done");
    });

    test("logs defaults to empty array when null is passed", () => {
        expect(buildSessionStatusPayload(makeSession(), null).logs).toEqual([]);
    });

    test("logs are passed through unchanged", () => {
        const logs = [{ msg: "started", level: "INFO" }];
        expect(buildSessionStatusPayload(makeSession(), logs).logs).toBe(logs);
    });

    test("globalCount is forwarded from the session", () => {
        expect(buildSessionStatusPayload(makeSession({ globalCount: 100 }), []).globalCount).toBe(100);
    });

    test("property: progress.done never exceeds progress.total", () => {
        fc.assert(
            fc.property(
                fc.array(
                    fc.record({ status: fc.constantFrom("OPEN", "DONE", "FAILED", "CANCELLED") }),
                    { minLength: 0, maxLength: 20 }
                ),
                (rawTasks) => {
                    const tasks = rawTasks.map((t, i) => ({ ...makeTask(t.status), index: i }));
                    const { progress } = buildSessionStatusPayload(
                        makeSession({ tasks, currentIndex: 0 }), []
                    );
                    expect(progress.done).toBeLessThanOrEqual(progress.total);
                }
            ),
            { numRuns: 300 }
        );
    });
});
