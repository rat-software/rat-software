const { decodeUrl, evaluateCaptchaSignals, computeIsFirstPage, computeRankOffset } = require('./src/content-logic');
const fc = require('fast-check');

// ---------------------------------------------------------------------------
// decodeUrl()
// ---------------------------------------------------------------------------
describe('decodeUrl()', () => {
    describe('null / N/A passthrough', () => {
        test('null → "N/A"', () => expect(decodeUrl(null, 'bing_base64')).toBe('N/A'));
        test('undefined → "N/A"', () => expect(decodeUrl(undefined, 'bing_base64')).toBe('N/A'));
        test('"N/A" → "N/A"', () => expect(decodeUrl('N/A', 'bing_base64')).toBe('N/A'));
        test('empty string → "N/A"', () => expect(decodeUrl('', 'bing_base64')).toBe('N/A'));
    });

    describe('no decoding method', () => {
        test('plain URL with null method → returned as-is', () => {
            expect(decodeUrl('https://example.com', null)).toBe('https://example.com');
        });
        test('plain URL with unknown method → returned as-is', () => {
            expect(decodeUrl('https://example.com', 'other_method')).toBe('https://example.com');
        });
        test('property: any non-bing_base64 method returns the original string', () => {
            fc.assert(fc.property(
                fc.string({ minLength: 1 }).filter(s => s !== 'N/A'),
                fc.string().filter(s => s !== 'bing_base64'),
                (url, method) => decodeUrl(url, method) === url
            ));
        });
    });

    describe('bing_base64 decoding', () => {
        // Bing wraps result URLs as: ?u=a1<url-safe-base64-of-target>
        // The helper strips 'a1', pads to a multiple of 4, converts url-safe → standard b64, then atob().
        function makeBingUrl(target) {
            const b64 = Buffer.from(target)
                .toString('base64')
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=/g, '');
            return `https://www.bing.com/ck/a?u=a1${b64}&ntb=1`;
        }

        test('decodes a standard ASCII target URL', () => {
            const url = makeBingUrl('https://example.com');
            expect(decodeUrl(url, 'bing_base64')).toBe('https://example.com');
        });

        test('decodes a target URL whose base64 needs padding (length % 4 !== 0)', () => {
            // 'https://example.org/x' — deliberately chosen so stripped b64 is not already % 4
            const target = 'https://example.org/x';
            expect(decodeUrl(makeBingUrl(target), 'bing_base64')).toBe(target);
        });

        test('decodes a target URL with a path and query string', () => {
            const target = 'https://example.com/path?q=hello&lang=de';
            expect(decodeUrl(makeBingUrl(target), 'bing_base64')).toBe(target);
        });

        test('no u param → returns original Bing URL unchanged', () => {
            const url = 'https://www.bing.com/ck/a?foo=bar';
            expect(decodeUrl(url, 'bing_base64')).toBe(url);
        });

        test('u param does not start with "a1" → returns original URL unchanged', () => {
            const url = 'https://www.bing.com/ck/a?u=b2SGVsbG8=&ntb=1';
            expect(decodeUrl(url, 'bing_base64')).toBe(url);
        });

        test('u param has invalid base64 after "a1" → returns original URL unchanged', () => {
            const url = 'https://www.bing.com/ck/a?u=a1!!!notbase64&ntb=1';
            expect(decodeUrl(url, 'bing_base64')).toBe(url);
        });

        test('malformed URL string with bing_base64 → returns original string unchanged', () => {
            const url = 'not a url at all';
            expect(decodeUrl(url, 'bing_base64')).toBe(url);
        });
    });
});

// ---------------------------------------------------------------------------
// evaluateCaptchaSignals()
// ---------------------------------------------------------------------------
describe('evaluateCaptchaSignals()', () => {
    // Truth table: hasUrlIndicator || (hasTextIndicator && hasSelector)
    describe('truth table — all 8 combinations', () => {
        test.each([
            [false, false, false, false],
            [false, false, true,  false],
            [false, true,  false, false],
            [false, true,  true,  true ],
            [true,  false, false, true ],
            [true,  false, true,  true ],
            [true,  true,  false, true ],
            [true,  true,  true,  true ],
        ])('url=%s text=%s sel=%s → %s', (url, text, sel, expected) => {
            expect(evaluateCaptchaSignals(url, text, sel)).toBe(expected);
        });
    });

    describe('property-based invariants', () => {
        test('always true when hasUrlIndicator is true', () => {
            fc.assert(fc.property(fc.boolean(), fc.boolean(), (text, sel) =>
                evaluateCaptchaSignals(true, text, sel) === true
            ));
        });

        test('always false when url and text indicators are both false', () => {
            fc.assert(fc.property(fc.boolean(), (sel) =>
                evaluateCaptchaSignals(false, false, sel) === false
            ));
        });

        test('always false when url indicator is false and selector is false', () => {
            fc.assert(fc.property(fc.boolean(), (text) =>
                evaluateCaptchaSignals(false, text, false) === false
            ));
        });
    });
});

// ---------------------------------------------------------------------------
// computeIsFirstPage()
// ---------------------------------------------------------------------------
describe('computeIsFirstPage()', () => {
    describe('first-page cases (expect true)', () => {
        test('no start, no first param → true', () =>
            expect(computeIsFirstPage(null, null)).toBe(true));
        test('start="0", first="1" → true', () =>
            expect(computeIsFirstPage('0', '1')).toBe(true));
        test('start="0", no first param → true', () =>
            expect(computeIsFirstPage('0', null)).toBe(true));
        test('no start param, first="1" → true', () =>
            expect(computeIsFirstPage(null, '1')).toBe(true));
        test('empty-string start treated as absent → true', () =>
            expect(computeIsFirstPage('', null)).toBe(true));
        test('empty-string first treated as absent → true', () =>
            expect(computeIsFirstPage(null, '')).toBe(true));
    });

    describe('subsequent-page cases (expect false)', () => {
        test('start="10" → false (Google page 2)', () =>
            expect(computeIsFirstPage('10', null)).toBe(false));
        test('start="20" → false (Google page 3)', () =>
            expect(computeIsFirstPage('20', null)).toBe(false));
        test('first="11" → false (Bing page 2)', () =>
            expect(computeIsFirstPage(null, '11')).toBe(false));
        test('start="10", first="11" → false', () =>
            expect(computeIsFirstPage('10', '11')).toBe(false));
    });
});

// ---------------------------------------------------------------------------
// computeRankOffset()
// ---------------------------------------------------------------------------
describe('computeRankOffset()', () => {
    describe('resets to 0', () => {
        test('different query → 0 (query changed)', () =>
            expect(computeRankOffset('cats', 'dogs', false, '10')).toBe(0));
        test('first page flag → 0 regardless of stored count', () =>
            expect(computeRankOffset('cats', 'cats', true, '10')).toBe(0));
        test('first page AND different query → 0', () =>
            expect(computeRankOffset('new', null, true, '5')).toBe(0));
        test('no previously stored query (lastQuery null) → 0', () =>
            expect(computeRankOffset('cats', null, false, '5')).toBe(0));
    });

    describe('returns accumulated count on subsequent pages', () => {
        test('same query, not first page, stored count "10" → 10', () =>
            expect(computeRankOffset('cats', 'cats', false, '10')).toBe(10));
        test('same query, not first page, stored count "42" → 42', () =>
            expect(computeRankOffset('cats', 'cats', false, '42')).toBe(42));
        test('same query, not first page, stored count "0" → 0', () =>
            expect(computeRankOffset('cats', 'cats', false, '0')).toBe(0));
        test('same query, not first page, no stored count (null) → 0', () =>
            expect(computeRankOffset('cats', 'cats', false, null)).toBe(0));
    });

    describe('property-based invariants', () => {
        test('offset is always a non-negative integer', () => {
            fc.assert(fc.property(
                fc.string(),
                fc.string(),
                fc.boolean(),
                fc.nat().map(n => String(n)),
                (cur, last, isFirst, stored) => {
                    const offset = computeRankOffset(cur, last, isFirst, stored);
                    return Number.isInteger(offset) && offset >= 0;
                }
            ));
        });

        test('offset is always 0 on the first page', () => {
            fc.assert(fc.property(
                fc.string(),
                fc.string(),
                fc.nat().map(n => String(n)),
                (cur, last, stored) =>
                    computeRankOffset(cur, last, true, stored) === 0
            ));
        });

        test('offset equals the stored count when query matches and page is not first', () => {
            fc.assert(fc.property(
                fc.string(),
                fc.nat(),
                (query, count) =>
                    computeRankOffset(query, query, false, String(count)) === count
            ));
        });
    });
});
