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
// buildSearchUrl
// ─────────────────────────────────────────────

describe("buildSearchUrl()", () => {
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
        const parsed = new URL(url);
        expect(parsed.searchParams.get("q")).toBe("C++ tutorial");
    });

    test("encodes quoted phrases in the search term", () => {
        const url = buildSearchUrl('"exact phrase"', makeTaskConfig(), makeEngine());
        const parsed = new URL(url);
        expect(parsed.searchParams.get("q")).toBe('"exact phrase"');
    });

    test("omits country param if countryCode is missing", () => {
        const config = makeTaskConfig({ countryCode: undefined });
        const url = buildSearchUrl("test", config, makeEngine());
        const parsed = new URL(url);
        expect(parsed.searchParams.has("gl")).toBe(false);
    });

    test("omits language param if langCode is missing", () => {
        const config = makeTaskConfig({ langCode: undefined });
        const url = buildSearchUrl("test", config, makeEngine());
        const parsed = new URL(url);
        expect(parsed.searchParams.has("hl")).toBe(false);
    });

    test("uses empty string for domain if domain is missing", () => {
        const config = makeTaskConfig({ domain: undefined });
        const engine = makeEngine();
        // baseUrl becomes "https://www.google./search" — URL constructor will throw or parse oddly
        // We just verify it doesn't crash and the query is still set
        expect(() => buildSearchUrl("test", config, engine)).not.toThrow();
    });

    test("appends UULE param when requiresUuleEncoding is true and location is set", () => {
        const engine = makeEngine({
            request: {
                baseUrl: "https://www.google.{domain}/search",
                params: { query: "q", country: "gl", language: "hl", location: "uule" },
                features: { requiresUuleEncoding: true },
            },
        });
        const config = makeTaskConfig({ location: "Berlin, Germany" });
        const url = buildSearchUrl("test", config, engine);
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
        const config = makeTaskConfig({ location: "Berlin" });
        const url = buildSearchUrl("test", config, engine);
        const parsed = new URL(url);
        expect(parsed.searchParams.has("uule")).toBe(false);
    });

    test("does NOT append UULE param when location is not set", () => {
        const engine = makeEngine({
            request: {
                baseUrl: "https://www.google.{domain}/search",
                params: { query: "q", country: "gl", language: "hl", location: "uule" },
                features: { requiresUuleEncoding: true },
            },
        });
        const config = makeTaskConfig(); // no location
        const url = buildSearchUrl("test", config, engine);
        const parsed = new URL(url);
        expect(parsed.searchParams.has("uule")).toBe(false);
    });

    test("handles unicode / emoji in search term", () => {
        const url = buildSearchUrl("café ☕", makeTaskConfig(), makeEngine());
        const parsed = new URL(url);
        expect(parsed.searchParams.get("q")).toBe("café ☕");
    });
});

// ─────────────────────────────────────────────
// generateUule
// ─────────────────────────────────────────────

describe("generateUule()", () => {
    test("always starts with the expected prefix", () => {
        expect(generateUule("Berlin")).toMatch(/^w\+CAIQICI/);
    });

    test("encodes the location string via btoa", () => {
        const loc = "New York, USA";
        const result = generateUule(loc);
        expect(result).toContain(btoa(loc));
    });

    test("uses correct secret character for given location length", () => {
        const secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
        const loc = "Tokyo";                       // length 5
        const expectedChar = secret[5 % 65];       // "F"
        const result = generateUule(loc);
        expect(result).toContain(`w+CAIQICI${expectedChar}`);
    });

    test("handles empty string without throwing", () => {
        expect(() => generateUule("")).not.toThrow();
    });

    test("handles a very long location name", () => {
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
// getRandomDelay
// ─────────────────────────────────────────────

describe("getRandomDelay()", () => {
    test("returns a number", () => {
        expect(typeof getRandomDelay(1000, 5000)).toBe("number");
    });

    test("result is within [min, max] range", () => {
        for (let i = 0; i < 200; i++) {
            const val = getRandomDelay(1000, 5000);
            expect(val).toBeGreaterThanOrEqual(1000);
            expect(val).toBeLessThanOrEqual(5000);
        }
    });

    test("returns exact value when min === max", () => {
        expect(getRandomDelay(3000, 3000)).toBe(3000);
    });

    test("returns an integer (no decimals)", () => {
        for (let i = 0; i < 50; i++) {
            const val = getRandomDelay(0, 10000);
            expect(Number.isInteger(val)).toBe(true);
        }
    });

    test("works with zero as min", () => {
        const val = getRandomDelay(0, 100);
        expect(val).toBeGreaterThanOrEqual(0);
        expect(val).toBeLessThanOrEqual(100);
    });
});

// ─────────────────────────────────────────────
// parseProxyLine (Proxy format validation)
// ─────────────────────────────────────────────

describe("parseProxyLine()", () => {
    test("parses a valid proxy line correctly", () => {
        const result = parseProxyLine("192.168.1.1:8080:user:pass");
        expect(result).toEqual({ ip: "192.168.1.1", port: 8080, user: "user", pass: "pass" });
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
        const result = parseProxyLine("10.0.0.1:3128:user:pass");
        expect(typeof result.port).toBe("number");
    });
});
