# CLAUDE.md – Result Assessment Tool (RAT)

Guidance for Claude (locally and in GitHub Actions, e.g. `.github/workflows/claude-fix-tests.yml`).
**Always write all output in English** – code comments, commit messages, PR descriptions,
issues and explanations.

## Project

RAT is an open-source toolbox by HAW Hamburg (Search Studies) for collecting, analyzing
and evaluating search results. Components:

| Folder | Contents |
|---|---|
| `rat-frontend/` | Flask web app (`app/`, `rat.py`, `wsgi.py`), PostgreSQL via SQLAlchemy |
| `rat-backend/` | Scraper/classifier controllers (`sources/`, `classifier/`, `query_sampler/`) |
| `rat-storage/` | Storage service for web pages/PDFs (`storage_service.py`, `clean_orphans.py`) |
| `rat-extension/` | Browser extension for scraping (`background.js`, `content.js`, `sidepanel.js`, `engines/`) |
| `install-database/` | SQL schema |
| `tests/` | All tests (Python + JavaScript) |

## Running tests

CI: `.github/workflows/unit-tests.yml` (workflow name "Unit Tests", Python 3.12, Node 24).

```bash
# Python – setup
pip install -r rat-frontend/requirements.txt
pip install pytest beautifulsoup4 lxml psutil langdetect textstat

# Python – unit tests
python -m pytest tests/ --ignore=tests/routes --ignore=tests/node_modules -v
# Python – route tests (Flask app with in-memory SQLite, see tests/routes/conftest.py)
python -m pytest tests/routes/ -v
# Single test
python -m pytest tests/test_helpers.py -v -k <name>

# JavaScript (Jest + fast-check + fake-indexeddb)
cd tests && npm ci && npm test
npx jest background.test.js -t "<name>"
```

Python unit tests and route tests run separately because the unit tests mock the `app`
package via `sys.modules`. Do not run them together in a single pytest invocation.

## Important quirks

- **`tests/src/*.js` are copies** of pure functions from `rat-extension/`
  (`utils.js` ← `background.js`, `content-logic.js` ← `content.js`,
  `sidepanel-logic.js` ← `sidepanel.js`, `db.js` ← IndexedDB part of `background.js`).
  If logic changes in the extension, the copy in `tests/src/` must be updated too – and
  vice versa. When fixing, always check both places and mention it in the PR.
- Python unit tests often import modules directly via `importlib` and mock Flask/DB.
  Do not assume a real database or network access in tests.
- Route tests set their environment variables in `tests/routes/conftest.py` *before*
  importing the app. Do not change that order.
- Never commit secrets (e.g. `rat-frontend/google-service-account.json`, `.env`).

## Rules for automated test fixes

1. Find the root cause and fix it **in the application code** – smallest sensible change.
2. Only change test code if the test is demonstrably wrong/outdated; justify it explicitly.
3. **Forbidden:** deleting tests, adding `skip`/`xfail`/`.skip`/`.only`, weakening
   assertions, or raising timeouts just to make tests pass.
4. No changes to `.github/`, dependency versions or deployment files
   (`setup.sh`, `*.service`, `deploy/`) unless that is clearly the root cause.
5. After the fix, run the affected tests **and** the complete respective suite.
6. Never push to existing branches; the workflow handles commit/push.
7. When unsure (flaky test, infrastructure, external services), do not change code –
   only document the analysis.

## Style

- Python: follow the existing style of the file. Write new comments/docstrings in English.
- JavaScript: vanilla JS (no build tools in the extension), CommonJS exports in `tests/src/`.
- PR descriptions, issues and explanations in English.
