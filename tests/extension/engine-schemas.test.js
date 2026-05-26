const fs   = require('fs');
const path = require('path');

const ENGINES_DIR = path.resolve(__dirname, '../../rat-extension/engines');
const INDEX_PATH  = path.join(ENGINES_DIR, 'index.json');

const VALID_DECODE_METHODS = new Set(['none', 'bing_base64']);
const VALID_SOURCE_TYPES   = new Set(['standard', 'attribute_based']);

const engineFiles = JSON.parse(fs.readFileSync(INDEX_PATH, 'utf8'));
const engines = engineFiles.map(filename => ({
    filename,
    config: JSON.parse(fs.readFileSync(path.join(ENGINES_DIR, filename), 'utf8')),
}));

// ---------------------------------------------------------------------------
// index.json
// ---------------------------------------------------------------------------
describe('index.json', () => {
    test('is a non-empty array', () => {
        expect(Array.isArray(engineFiles)).toBe(true);
        expect(engineFiles.length).toBeGreaterThan(0);
    });

    test('contains only strings ending in .json', () => {
        engineFiles.forEach(f => {
            expect(typeof f).toBe('string');
            expect(f).toMatch(/\.json$/);
        });
    });

    test('has no duplicate entries', () => {
        expect(new Set(engineFiles).size).toBe(engineFiles.length);
    });

    test('every listed file exists on disk', () => {
        engineFiles.forEach(f => {
            expect(fs.existsSync(path.join(ENGINES_DIR, f))).toBe(true);
        });
    });

    test('no engine JSON file in the directory is missing from the index', () => {
        const onDisk  = fs.readdirSync(ENGINES_DIR).filter(f => f.endsWith('.json') && f !== 'index.json');
        const inIndex = new Set(engineFiles);
        onDisk.forEach(f => expect(inIndex.has(f)).toBe(true));
    });
});

// ---------------------------------------------------------------------------
// Per-engine structural validation
// ---------------------------------------------------------------------------
describe.each(engines)('$filename', ({ filename, config }) => {
    const eng = config.engine;
    const req = config.request;
    const beh = config.behavior;
    const cap = config.captcha;
    const sel = config.selectors;

    test('manifest_version is 1', () =>
        expect(config.manifest_version).toBe(1));

    // --- engine metadata ---
    describe('engine', () => {
        test('id is a non-empty string', () => {
            expect(typeof eng.id).toBe('string');
            expect(eng.id.length).toBeGreaterThan(0);
        });

        test('id matches the filename stem', () =>
            expect(eng.id).toBe(filename.replace('.json', '')));

        test('name is a non-empty string', () => {
            expect(typeof eng.name).toBe('string');
            expect(eng.name.length).toBeGreaterThan(0);
        });

        test('author is a non-empty string', () => {
            expect(typeof eng.author).toBe('string');
            expect(eng.author.length).toBeGreaterThan(0);
        });

        test('version is a non-empty string', () => {
            expect(typeof eng.version).toBe('string');
            expect(eng.version.length).toBeGreaterThan(0);
        });

        test('description is a non-empty string', () => {
            expect(typeof eng.description).toBe('string');
            expect(eng.description.length).toBeGreaterThan(0);
        });
    });

    // --- request ---
    describe('request', () => {
        test('baseUrl starts with "https://"', () => {
            expect(typeof req.baseUrl).toBe('string');
            expect(req.baseUrl.startsWith('https://')).toBe(true);
        });

        test('params.query is a non-empty string', () => {
            expect(typeof req.params.query).toBe('string');
            expect(req.params.query.length).toBeGreaterThan(0);
        });

        test('features.requiresUuleEncoding is a boolean', () =>
            expect(typeof req.features.requiresUuleEncoding).toBe('boolean'));

        test('features.urlDecodingMethod is "none" or "bing_base64"', () =>
            expect(VALID_DECODE_METHODS.has(req.features.urlDecodingMethod)).toBe(true));

        test('if requiresUuleEncoding → params.location must be a non-empty string', () => {
            if (req.features.requiresUuleEncoding) {
                expect(typeof req.params.location).toBe('string');
                expect(req.params.location.length).toBeGreaterThan(0);
            }
        });

        describe('supportedCountries', () => {
            test('is a non-empty array', () => {
                expect(Array.isArray(req.supportedCountries)).toBe(true);
                expect(req.supportedCountries.length).toBeGreaterThan(0);
            });

            test('each entry has a non-empty code and name', () => {
                req.supportedCountries.forEach(c => {
                    expect(typeof c.code).toBe('string');
                    expect(c.code.length).toBeGreaterThan(0);
                    expect(typeof c.name).toBe('string');
                    expect(c.name.length).toBeGreaterThan(0);
                });
            });

            test('country codes are unique within this engine', () => {
                const codes = req.supportedCountries.map(c => c.code);
                expect(new Set(codes).size).toBe(codes.length);
            });

            test('if requiresUuleEncoding → each country must have a non-empty domain', () => {
                if (req.features.requiresUuleEncoding) {
                    req.supportedCountries.forEach(c => {
                        expect(typeof c.domain).toBe('string');
                        expect(c.domain.length).toBeGreaterThan(0);
                    });
                }
            });
        });

        describe('supportedLanguages', () => {
            test('is a non-empty array', () => {
                expect(Array.isArray(req.supportedLanguages)).toBe(true);
                expect(req.supportedLanguages.length).toBeGreaterThan(0);
            });

            test('each entry has a non-empty code and name', () => {
                req.supportedLanguages.forEach(l => {
                    expect(typeof l.code).toBe('string');
                    expect(l.code.length).toBeGreaterThan(0);
                    expect(typeof l.name).toBe('string');
                    expect(l.name.length).toBeGreaterThan(0);
                });
            });

            test('language codes are unique within this engine', () => {
                const codes = req.supportedLanguages.map(l => l.code);
                expect(new Set(codes).size).toBe(codes.length);
            });
        });
    });

    // --- behavior ---
    describe('behavior', () => {
        test('cookieConsentSelectors is an array of strings', () => {
            expect(Array.isArray(beh.cookieConsentSelectors)).toBe(true);
            beh.cookieConsentSelectors.forEach(s => expect(typeof s).toBe('string'));
        });

        test('popupDismissSelectors is an array of strings', () => {
            expect(Array.isArray(beh.popupDismissSelectors)).toBe(true);
            beh.popupDismissSelectors.forEach(s => expect(typeof s).toBe('string'));
        });

        test('stickyHeaderSelectors is an array of strings', () => {
            expect(Array.isArray(beh.stickyHeaderSelectors)).toBe(true);
            beh.stickyHeaderSelectors.forEach(s => expect(typeof s).toBe('string'));
        });

        test('aiExpandSelectors (when present) is an array of strings', () => {
            if (beh.aiExpandSelectors !== undefined) {
                expect(Array.isArray(beh.aiExpandSelectors)).toBe(true);
                beh.aiExpandSelectors.forEach(s => expect(typeof s).toBe('string'));
            }
        });

        test('aiExpandKeywords (when present) is an array of strings', () => {
            if (beh.aiExpandKeywords !== undefined) {
                expect(Array.isArray(beh.aiExpandKeywords)).toBe(true);
                beh.aiExpandKeywords.forEach(s => expect(typeof s).toBe('string'));
            }
        });
    });

    // --- captcha ---
    describe('captcha', () => {
        test('urlIndicators is an array of strings', () => {
            expect(Array.isArray(cap.urlIndicators)).toBe(true);
            cap.urlIndicators.forEach(s => expect(typeof s).toBe('string'));
        });

        test('textIndicators is an array of strings', () => {
            expect(Array.isArray(cap.textIndicators)).toBe(true);
            cap.textIndicators.forEach(s => expect(typeof s).toBe('string'));
        });

        test('selectors is an array of strings', () => {
            expect(Array.isArray(cap.selectors)).toBe(true);
            cap.selectors.forEach(s => expect(typeof s).toBe('string'));
        });
    });

    // --- selectors ---
    describe('selectors', () => {
        describe('pagination', () => {
            test('nextButton is a non-empty string', () => {
                expect(typeof sel.pagination.nextButton).toBe('string');
                expect(sel.pagination.nextButton.length).toBeGreaterThan(0);
            });
        });

        describe('organic', () => {
            test('container is a non-empty string', () => {
                expect(typeof sel.organic.container).toBe('string');
                expect(sel.organic.container.length).toBeGreaterThan(0);
            });

            test('title is a non-empty string', () => {
                expect(typeof sel.organic.title).toBe('string');
                expect(sel.organic.title.length).toBeGreaterThan(0);
            });

            test('url is a non-empty string', () => {
                expect(typeof sel.organic.url).toBe('string');
                expect(sel.organic.url.length).toBeGreaterThan(0);
            });

            test('snippet has a string selector', () => {
                expect(typeof sel.organic.snippet).toBe('object');
                expect(typeof sel.organic.snippet.selector).toBe('string');
            });
        });

        describe('ads', () => {
            test('container is a non-empty string', () => {
                expect(typeof sel.ads.container).toBe('string');
                expect(sel.ads.container.length).toBeGreaterThan(0);
            });

            test('title is a non-empty string', () => {
                expect(typeof sel.ads.title).toBe('string');
                expect(sel.ads.title.length).toBeGreaterThan(0);
            });

            test('url is a non-empty string', () => {
                expect(typeof sel.ads.url).toBe('string');
                expect(sel.ads.url.length).toBeGreaterThan(0);
            });

            test('snippet has a string selector', () => {
                expect(typeof sel.ads.snippet).toBe('object');
                expect(typeof sel.ads.snippet.selector).toBe('string');
            });
        });

        describe('ai_overview', () => {
            test('container is a non-empty string', () => {
                expect(typeof sel.ai_overview.container).toBe('string');
                expect(sel.ai_overview.container.length).toBeGreaterThan(0);
            });

            test('sources is an array', () =>
                expect(Array.isArray(sel.ai_overview.sources)).toBe(true));

            test('each source has a valid type and non-empty container', () => {
                sel.ai_overview.sources.forEach(src => {
                    expect(VALID_SOURCE_TYPES.has(src.type)).toBe(true);
                    expect(typeof src.container).toBe('string');
                    expect(src.container.length).toBeGreaterThan(0);
                });
            });

            test('standard sources have string title and url fields', () => {
                sel.ai_overview.sources
                    .filter(s => s.type === 'standard')
                    .forEach(src => {
                        expect(typeof src.title).toBe('string');
                        expect(typeof src.url).toBe('string');
                    });
            });

            test('attribute_based sources have string titleAttribute and urlAttribute', () => {
                sel.ai_overview.sources
                    .filter(s => s.type === 'attribute_based')
                    .forEach(src => {
                        expect(typeof src.titleAttribute).toBe('string');
                        expect(typeof src.urlAttribute).toBe('string');
                    });
            });
        });
    });
});

// ---------------------------------------------------------------------------
// Cross-engine invariants
// ---------------------------------------------------------------------------
describe('cross-engine invariants', () => {
    test('engine.id values are unique across all engines', () => {
        const ids = engines.map(e => e.config.engine.id);
        expect(new Set(ids).size).toBe(ids.length);
    });

    test('engine.name values are unique across all engines', () => {
        const names = engines.map(e => e.config.engine.name);
        expect(new Set(names).size).toBe(names.length);
    });
});
