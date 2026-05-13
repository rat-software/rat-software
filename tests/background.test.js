const fc = require("fast-check");
const { generateUule, buildSearchUrl, getRandomDelay, parseProxyLine,
        parseProxyList, buildProxyConfig, selectRandomProxy, getRetryDelay } = require('./src/utils');
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
