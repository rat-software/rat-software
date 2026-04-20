const fc = require("fast-check");
const { generateUule, buildSearchUrl, getRandomDelay, parseProxyLine } = require('./src/utils');

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
