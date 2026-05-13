const fc = require("fast-check");
const {
    filterTasks, paginateTasks,
    computeProgress, computeProgressPercent,
    getStatusDisplay, getSessionCardClass,
    getPlayPauseBtnState,
    getTaskDeleteVisibility, getTaskRetryVisibility,
    getLogColor,
    escapeCSV, getExportFilename,
    clampZoom,
    parseQueries, parseKeywordsFromFileContent,
    shouldUpdateStatus,
    delaysToMs,
    applyDeleteTask, applyRetryTask,
    TASKS_PER_PAGE,
} = require('./src/sidepanel-logic');

// ─────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────

const STATUSES = ["OPEN", "RUNNING", "DONE", "FAILED", "CANCELLED", "PAUSED_CAPTCHA"];

function makeTask(index, status = "OPEN", overrides = {}) {
    return { index, term: `query_${index}`, engine: "Google", country: "US", status, retryCount: 0, ...overrides };
}

function makeTasks(statusList) {
    return statusList.map((s, i) => makeTask(i, s));
}

// ─────────────────────────────────────────────
// filterTasks — UI-Event: Filter-Button click
// ─────────────────────────────────────────────

describe("filterTasks() — task filter state", () => {
    const tasks = makeTasks(["OPEN", "DONE", "FAILED", "OPEN", "CANCELLED", "DONE"]);

    test("ALL returns all tasks", () => {
        expect(filterTasks(tasks, "ALL")).toHaveLength(6);
    });

    test("DONE returns only done tasks", () => {
        const result = filterTasks(tasks, "DONE");
        expect(result).toHaveLength(2);
        result.forEach(t => expect(t.status).toBe("DONE"));
    });

    test("FAILED returns only failed tasks", () => {
        const result = filterTasks(tasks, "FAILED");
        expect(result).toHaveLength(1);
        expect(result[0].status).toBe("FAILED");
    });

    test("OPEN returns only open tasks", () => {
        expect(filterTasks(tasks, "OPEN")).toHaveLength(2);
    });

    test("unknown filter returns empty array", () => {
        expect(filterTasks(tasks, "NONEXISTENT")).toHaveLength(0);
    });

    test("empty task list always returns empty array", () => {
        STATUSES.forEach(s => expect(filterTasks([], s)).toHaveLength(0));
    });

    test("does not mutate the original array", () => {
        const original = makeTasks(["OPEN", "DONE"]);
        filterTasks(original, "DONE");
        expect(original).toHaveLength(2);
    });

    test("property: filter(ALL).length === filter(DONE)+filter(OPEN)+... for disjoint statuses", () => {
        fc.assert(
            fc.property(
                fc.array(fc.constantFrom(...STATUSES), { minLength: 0, maxLength: 30 }),
                (statusList) => {
                    const tasks = makeTasks(statusList);
                    const totalFiltered = STATUSES.reduce((sum, s) => sum + filterTasks(tasks, s).length, 0);
                    expect(totalFiltered).toBe(tasks.length);
                }
            ),
            { numRuns: 200 }
        );
    });
});

// ─────────────────────────────────────────────
// paginateTasks — State: currentTaskPage
// ─────────────────────────────────────────────

describe("paginateTasks() — pagination state", () => {
    const fiftyFiveTasks = makeTasks(Array(55).fill("OPEN"));

    test("first page returns up to TASKS_PER_PAGE items", () => {
        const { tasks } = paginateTasks(fiftyFiveTasks, 1);
        expect(tasks).toHaveLength(TASKS_PER_PAGE);
    });

    test("second page returns remainder", () => {
        const { tasks } = paginateTasks(fiftyFiveTasks, 2);
        expect(tasks).toHaveLength(5);
    });

    test("totalPages is correct", () => {
        expect(paginateTasks(fiftyFiveTasks, 1).totalPages).toBe(2);
    });

    test("page beyond totalPages is clamped to last page", () => {
        const { currentPage } = paginateTasks(fiftyFiveTasks, 99);
        expect(currentPage).toBe(2);
    });

    test("page below 1 is clamped to 1", () => {
        const { currentPage } = paginateTasks(fiftyFiveTasks, -5);
        expect(currentPage).toBe(1);
    });

    test("empty list returns empty tasks and totalPages 1", () => {
        const { tasks, totalPages } = paginateTasks([], 1);
        expect(tasks).toHaveLength(0);
        expect(totalPages).toBe(1);
    });

    test("exactly TASKS_PER_PAGE items produces totalPages=1", () => {
        const exact = makeTasks(Array(TASKS_PER_PAGE).fill("OPEN"));
        expect(paginateTasks(exact, 1).totalPages).toBe(1);
    });

    test("TASKS_PER_PAGE+1 items produces totalPages=2", () => {
        const one_over = makeTasks(Array(TASKS_PER_PAGE + 1).fill("OPEN"));
        expect(paginateTasks(one_over, 1).totalPages).toBe(2);
    });

    test("property: paginated tasks are always a subset of filtered tasks", () => {
        fc.assert(
            fc.property(
                fc.integer({ min: 0, max: 200 }),
                fc.integer({ min: 1, max: 10 }),
                (count, page) => {
                    const tasks = makeTasks(Array(count).fill("OPEN"));
                    const { tasks: paged } = paginateTasks(tasks, page);
                    expect(paged.length).toBeLessThanOrEqual(Math.min(count, TASKS_PER_PAGE));
                }
            ),
            { numRuns: 300 }
        );
    });
});

// ─────────────────────────────────────────────
// computeProgress — State: Fortschrittsanzeige
// ─────────────────────────────────────────────

describe("computeProgress()", () => {
    test("counts done tasks correctly", () => {
        const tasks = makeTasks(["DONE", "DONE", "OPEN", "FAILED"]);
        expect(computeProgress(tasks).done).toBe(2);
    });

    test("total equals full task count", () => {
        const tasks = makeTasks(["DONE", "OPEN", "FAILED"]);
        expect(computeProgress(tasks).total).toBe(3);
    });

    test("empty tasks returns done=0, total=0", () => {
        expect(computeProgress([])).toEqual({ done: 0, total: 0 });
    });

    test("all done tasks returns done===total", () => {
        const tasks = makeTasks(["DONE", "DONE"]);
        const { done, total } = computeProgress(tasks);
        expect(done).toBe(total);
    });
});

describe("computeProgressPercent()", () => {
    test("50% when half done", () => {
        expect(computeProgressPercent(5, 10)).toBe(50);
    });

    test("0 when total is 0 (no division by zero)", () => {
        expect(computeProgressPercent(0, 0)).toBe(0);
    });

    test("100% when all done", () => {
        expect(computeProgressPercent(10, 10)).toBe(100);
    });

    test("0% when nothing done", () => {
        expect(computeProgressPercent(0, 10)).toBe(0);
    });
});

// ─────────────────────────────────────────────
// getStatusDisplay — State-Management: Status-Anzeige
// ─────────────────────────────────────────────

describe("getStatusDisplay()", () => {
    test("PAUSED_CAPTCHA shows human-readable text", () => {
        const { text } = getStatusDisplay("PAUSED_CAPTCHA");
        expect(text).toBe("PAUSED (CAPTCHA)");
    });

    test("PAUSED_CAPTCHA shows red color", () => {
        expect(getStatusDisplay("PAUSED_CAPTCHA").color).toBe("#dc3545");
    });

    test("all other statuses pass through as-is", () => {
        ["OPEN", "RUNNING", "DONE", "PAUSED", "FAILED"].forEach(s => {
            expect(getStatusDisplay(s).text).toBe(s);
        });
    });

    test("non-captcha statuses use black color", () => {
        ["RUNNING", "DONE", "PAUSED"].forEach(s => {
            expect(getStatusDisplay(s).color).toBe("black");
        });
    });
});

// ─────────────────────────────────────────────
// getSessionCardClass — UI-Rendering
// ─────────────────────────────────────────────

describe("getSessionCardClass()", () => {
    test("RUNNING adds session-running class", () => {
        expect(getSessionCardClass("RUNNING")).toContain("session-running");
    });

    test("PAUSED_CAPTCHA adds session-paused-captcha class", () => {
        expect(getSessionCardClass("PAUSED_CAPTCHA")).toContain("session-paused-captcha");
    });

    test("all cards have base session-card class", () => {
        STATUSES.forEach(s => {
            expect(getSessionCardClass(s)).toContain("session-card");
        });
    });

    test("DONE has no extra class", () => {
        expect(getSessionCardClass("DONE")).toBe("session-card");
    });
});

// ─────────────────────────────────────────────
// getPlayPauseBtnState — UI-Event: Play/Pause Button
// ─────────────────────────────────────────────

describe("getPlayPauseBtnState()", () => {
    test("RUNNING state shows Pause", () => {
        expect(getPlayPauseBtnState("RUNNING").text).toBe("Pause");
    });

    test("non-RUNNING state shows Resume / Start", () => {
        ["PAUSED", "DONE", "OPEN"].forEach(s => {
            expect(getPlayPauseBtnState(s).text).toBe("Resume / Start");
        });
    });

    test("RUNNING adds btn-primary", () => {
        expect(getPlayPauseBtnState("RUNNING").add).toBe("btn-primary");
    });

    test("RUNNING removes btn-success", () => {
        expect(getPlayPauseBtnState("RUNNING").remove).toBe("btn-success");
    });

    test("PAUSED adds btn-success", () => {
        expect(getPlayPauseBtnState("PAUSED").add).toBe("btn-success");
    });
});

// ─────────────────────────────────────────────
// Task Item Visibility — UI-Rendering
// ─────────────────────────────────────────────

describe("getTaskDeleteVisibility()", () => {
    test("OPEN task shows delete button", () => {
        expect(getTaskDeleteVisibility("OPEN")).toBe("visible");
    });

    test("FAILED task shows delete button", () => {
        expect(getTaskDeleteVisibility("FAILED")).toBe("visible");
    });

    test("DONE task hides delete button", () => {
        expect(getTaskDeleteVisibility("DONE")).toBe("hidden");
    });

    test("CANCELLED task hides delete button", () => {
        expect(getTaskDeleteVisibility("CANCELLED")).toBe("hidden");
    });

    test("RUNNING task hides delete button", () => {
        expect(getTaskDeleteVisibility("RUNNING")).toBe("hidden");
    });
});

describe("getTaskRetryVisibility()", () => {
    test("FAILED task shows retry button", () => {
        expect(getTaskRetryVisibility("FAILED")).toBe("inline-block");
    });

    test("OPEN task hides retry button", () => {
        expect(getTaskRetryVisibility("OPEN")).toBe("none");
    });

    test("DONE task hides retry button", () => {
        expect(getTaskRetryVisibility("DONE")).toBe("none");
    });
});

// ─────────────────────────────────────────────
// getLogColor — UI-Rendering
// ─────────────────────────────────────────────

describe("getLogColor()", () => {
    test("WARN is yellow-ish", () => {
        expect(getLogColor("WARN")).toBe("#856404");
    });

    test("ERROR is red", () => {
        expect(getLogColor("ERROR")).toBe("#721c24");
    });

    test("INFO and default are dark grey", () => {
        expect(getLogColor("INFO")).toBe("#333");
        expect(getLogColor(undefined)).toBe("#333");
        expect(getLogColor("SUCCESS")).toBe("#333");
    });
});

// ─────────────────────────────────────────────
// escapeCSV — Export-Logik
// ─────────────────────────────────────────────

describe("escapeCSV()", () => {
    test("wraps value in double quotes", () => {
        expect(escapeCSV("hello")).toBe('"hello"');
    });

    test("escapes internal double quotes by doubling them", () => {
        expect(escapeCSV('say "hi"')).toBe('"say ""hi"""');
    });

    test("returns empty quoted string for null", () => {
        expect(escapeCSV(null)).toBe('""');
    });

    test("returns empty quoted string for undefined", () => {
        expect(escapeCSV(undefined)).toBe('""');
    });

    test("converts numbers to string", () => {
        expect(escapeCSV(42)).toBe('"42"');
    });

    test("handles commas safely (no unquoted commas)", () => {
        const result = escapeCSV("a, b, c");
        expect(result.startsWith('"')).toBe(true);
        expect(result.endsWith('"')).toBe(true);
    });

    test("handles newlines inside a value", () => {
        expect(escapeCSV("line1\nline2")).toBe('"line1\nline2"');
    });

    test("property: result always starts and ends with a double quote", () => {
        fc.assert(
            fc.property(fc.string(), (s) => {
                const r = escapeCSV(s);
                expect(r.startsWith('"')).toBe(true);
                expect(r.endsWith('"')).toBe(true);
            }),
            { numRuns: 500 }
        );
    });
});

describe("getExportFilename()", () => {
    test("contains the session name (sanitized)", () => {
        expect(getExportFilename("MyStudy")).toContain("MyStudy");
    });

    test("replaces non-word characters with underscore", () => {
        expect(getExportFilename("My Study 2024!")).toContain("My_Study_2024_");
    });

    test("always ends with .zip", () => {
        expect(getExportFilename("test")).toMatch(/\.zip$/);
    });

    test("starts with RAT_Export_", () => {
        expect(getExportFilename("foo")).toMatch(/^RAT_Export_/);
    });
});

// ─────────────────────────────────────────────
// clampZoom — UI-Event: Zoom Buttons
// ─────────────────────────────────────────────

describe("clampZoom()", () => {
    test("zoom in increases value", () => {
        expect(clampZoom(1.0, 0.1)).toBeCloseTo(1.1);
    });

    test("zoom out decreases value", () => {
        expect(clampZoom(1.0, -0.1)).toBeCloseTo(0.9);
    });

    test("cannot exceed 2.0", () => {
        expect(clampZoom(1.95, 0.1)).toBe(2.0);
        expect(clampZoom(2.0, 0.1)).toBe(2.0);
    });

    test("cannot go below 0.8", () => {
        expect(clampZoom(0.85, -0.1)).toBe(0.8);
        expect(clampZoom(0.8, -0.1)).toBe(0.8);
    });

    test("stays within bounds for any delta (property)", () => {
        fc.assert(
            fc.property(
                fc.float({ min: Math.fround(0.8), max: Math.fround(2.0) }),
                fc.float({ min: Math.fround(-1.0), max: Math.fround(1.0) }),
                (zoom, delta) => {
                    const result = clampZoom(zoom, delta);
                    expect(result).toBeGreaterThanOrEqual(0.8);
                    expect(result).toBeLessThanOrEqual(2.0);
                }
            ),
            { numRuns: 300 }
        );
    });
});

// ─────────────────────────────────────────────
// parseQueries — UI-Event: Textarea Input
// ─────────────────────────────────────────────

describe("parseQueries()", () => {
    test("splits by newline", () => {
        expect(parseQueries("a\nb\nc")).toHaveLength(3);
    });

    test("filters blank lines", () => {
        expect(parseQueries("a\n\nb")).toHaveLength(2);
    });

    test("filters whitespace-only lines", () => {
        expect(parseQueries("a\n   \nb")).toHaveLength(2);
    });

    test("empty string returns empty array", () => {
        expect(parseQueries("")).toHaveLength(0);
    });

    test("single query returns one-element array", () => {
        expect(parseQueries("climate change")).toHaveLength(1);
    });
});

describe("parseKeywordsFromFileContent() — Drag & Drop", () => {
    test("splits by newline", () => {
        expect(parseKeywordsFromFileContent("a\nb")).toHaveLength(2);
    });

    test("splits by comma", () => {
        expect(parseKeywordsFromFileContent("a,b,c")).toHaveLength(3);
    });

    test("splits by semicolon", () => {
        expect(parseKeywordsFromFileContent("a;b")).toHaveLength(2);
    });

    test("trims whitespace from each keyword", () => {
        expect(parseKeywordsFromFileContent("  hello  ,  world  ")[0]).toBe("hello");
    });

    test("filters empty entries", () => {
        expect(parseKeywordsFromFileContent("a,,b")).toHaveLength(2);
    });

    test("handles mixed delimiters", () => {
        expect(parseKeywordsFromFileContent("a\nb,c;d")).toHaveLength(4);
    });
});

// ─────────────────────────────────────────────
// shouldUpdateStatus — State Guard
// ─────────────────────────────────────────────

describe("shouldUpdateStatus()", () => {
    test("returns true when IDs match", () => {
        expect(shouldUpdateStatus("sess_1", "sess_1")).toBe(true);
    });

    test("returns false when IDs differ", () => {
        expect(shouldUpdateStatus("sess_1", "sess_2")).toBe(false);
    });

    test("returns false when currentSessionId is null", () => {
        expect(shouldUpdateStatus("sess_1", null)).toBe(false);
    });

    test("returns false when both are null", () => {
        expect(shouldUpdateStatus(null, null)).toBe(true);
    });
});

// ─────────────────────────────────────────────
// delaysToMs — State: Delay-Konvertierung
// ─────────────────────────────────────────────

describe("delaysToMs()", () => {
    test("converts seconds to milliseconds", () => {
        expect(delaysToMs(3, 8)).toEqual({ min: 3000, max: 8000 });
    });

    test("zero stays zero", () => {
        expect(delaysToMs(0, 0)).toEqual({ min: 0, max: 0 });
    });

    test("property: min always <= max if input min <= max", () => {
        fc.assert(
            fc.property(
                fc.integer({ min: 0, max: 600 }),
                fc.integer({ min: 0, max: 600 }),
                (a, b) => {
                    const minSec = Math.min(a, b);
                    const maxSec = Math.max(a, b);
                    const { min, max } = delaysToMs(minSec, maxSec);
                    expect(min).toBeLessThanOrEqual(max);
                }
            ),
            { numRuns: 300 }
        );
    });
});

// ─────────────────────────────────────────────
// applyDeleteTask / applyRetryTask — Optimistic UI Updates
// ─────────────────────────────────────────────

describe("applyDeleteTask() — optimistische UI-Aktualisierung", () => {
    test("sets task status to CANCELLED", () => {
        const tasks = [makeTask(0, "OPEN"), makeTask(1, "OPEN")];
        applyDeleteTask(tasks, 0);
        expect(tasks[0].status).toBe("CANCELLED");
    });

    test("other tasks are not affected", () => {
        const tasks = [makeTask(0, "OPEN"), makeTask(1, "OPEN")];
        applyDeleteTask(tasks, 0);
        expect(tasks[1].status).toBe("OPEN");
    });

    test("does nothing if index not found", () => {
        const tasks = [makeTask(0, "OPEN")];
        expect(() => applyDeleteTask(tasks, 99)).not.toThrow();
        expect(tasks[0].status).toBe("OPEN");
    });
});

describe("applyRetryTask() — optimistische UI-Aktualisierung", () => {
    test("sets task status to OPEN", () => {
        const tasks = [makeTask(0, "FAILED", { retryCount: 3 })];
        applyRetryTask(tasks, 0);
        expect(tasks[0].status).toBe("OPEN");
    });

    test("resets retryCount to 0", () => {
        const tasks = [makeTask(0, "FAILED", { retryCount: 3 })];
        applyRetryTask(tasks, 0);
        expect(tasks[0].retryCount).toBe(0);
    });

    test("other tasks are not affected", () => {
        const tasks = [makeTask(0, "FAILED"), makeTask(1, "DONE")];
        applyRetryTask(tasks, 0);
        expect(tasks[1].status).toBe("DONE");
    });

    test("does nothing if index not found", () => {
        const tasks = [makeTask(0, "FAILED")];
        expect(() => applyRetryTask(tasks, 99)).not.toThrow();
        expect(tasks[0].status).toBe("FAILED");
    });
});
