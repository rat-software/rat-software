"""

Drei Stufen:
1. Selenium (SeleniumBase, uc=True)
2. Playwright/patchright
3. curl

Nutzung:
    python demo_scraper.py failed_source.csv results.csv
"""

import asyncio
import random
import re
import subprocess
import sys
import time
import csv
from collections import Counter

try:
    from seleniumbase import Driver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from patchright.async_api import async_playwright
    ENGINE = "patchright"
except ImportError:
    from playwright.async_api import async_playwright
    ENGINE = "playwright"

SELENIUM_TIMEOUT = 45
PLAYWRIGHT_TIMEOUT = 25
CURL_TIMEOUT = 15
CONCURRENCY = 4
MIN_TEXT_LEN = 200

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# 404-Phrasen
SOFT_404_RE = re.compile(
    r"(?:404|page not found|seite nicht gefunden|not found)", re.IGNORECASE
)


def evaluate_success(status_code, text_sample, text_len):
    if status_code is not None and str(status_code) not in ("200", "202", "204"):
        return False, f"status_code={status_code}"
    if SOFT_404_RE.search(text_sample or ""):
        return False, "soft_404"
    if text_len is not None and text_len < MIN_TEXT_LEN:
        return False, "thin_content"
    return True, "verified_ok"


# ---------------------------------------------------------------------------
# Tier 1: Selenium
# ---------------------------------------------------------------------------
def _selenium_attempt_sync(url: str) -> dict:
    if not SELENIUM_AVAILABLE:
        return {"error": "seleniumbase nicht installiert"}
    driver = None
    try:
        driver = Driver(browser="chrome", uc=True, headless2=True, no_sandbox=True, agent=UA)
        driver.set_page_load_timeout(SELENIUM_TIMEOUT)
        driver.get(url)
        time.sleep(1.5)
        text_sample = driver.execute_script(
            "return document.body ? document.body.innerText.trim().slice(0,1000) : '';"
        )
        text_len = driver.execute_script(
            "return document.body ? document.body.innerText.trim().length : 0;"
        )
        # kein verlaesslicher Status-Code aus Selenium -> rein inhaltliche Bewertung
        return {"status_code": None, "text_sample": text_sample, "text_len": text_len}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


async def selenium_attempt(url: str) -> dict:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_selenium_attempt_sync, url), timeout=SELENIUM_TIMEOUT + 15
        )
    except asyncio.TimeoutError:
        return {"error": "selenium_timeout"}


# ---------------------------------------------------------------------------
# Tier 2: Playwright/patchright
# ---------------------------------------------------------------------------
async def playwright_attempt(browser, url: str) -> dict:
    try:
        context = await browser.new_context(user_agent=UA, locale="de-DE")
        page = await context.new_page()
        resp = await page.goto(url, timeout=PLAYWRIGHT_TIMEOUT * 1000, wait_until="domcontentloaded")
        await page.wait_for_timeout(800)
        status_code = resp.status if resp else None
        text_sample = await page.evaluate("() => document.body ? document.body.innerText.trim().slice(0,1000) : ''")
        text_len = await page.evaluate("() => document.body ? document.body.innerText.trim().length : 0")
        await context.close()
        return {"status_code": status_code, "text_sample": text_sample, "text_len": text_len}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
# Tier 3: curl
# ---------------------------------------------------------------------------
def _curl_attempt_sync(url: str) -> dict:
    marker = "__STATUS__:"
    cmd = [
        "curl", "-s", "-L", "-A", UA,
        "--max-time", str(CURL_TIMEOUT), "--connect-timeout", "8",
        "-w", f"\n{marker}%{{http_code}}", url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CURL_TIMEOUT + 5)
        out = proc.stdout
        body, _, status_part = out.rpartition(marker) if marker in out else (out, "", None)
        status_code = status_part.strip() if status_part else None
        text_only = re.sub(r"<[^>]+>", " ", body)
        text_only = re.sub(r"\s+", " ", text_only).strip()
        return {"status_code": status_code, "text_sample": text_only[:1000], "text_len": len(text_only)}
    except Exception as e:
        return {"error": str(e)}


async def curl_attempt(url: str) -> dict:
    return await asyncio.to_thread(_curl_attempt_sync, url)


# ---------------------------------------------------------------------------
# Orchestrator: Selenium -> Playwright/patchright -> curl
# ---------------------------------------------------------------------------
async def scrape_url(url: str, browser) -> dict:
    r = await selenium_attempt(url)
    if not r.get("error"):
        ok, reason = evaluate_success(r.get("status_code"), r.get("text_sample"), r.get("text_len"))
        if ok:
            return {"url": url, "success": True, "engine_used": "selenium", "reason": reason}

    r = await playwright_attempt(browser, url)
    if not r.get("error"):
        ok, reason = evaluate_success(r.get("status_code"), r.get("text_sample"), r.get("text_len"))
        if ok:
            return {"url": url, "success": True, "engine_used": "playwright", "reason": reason}

    r = await curl_attempt(url)
    if r.get("error"):
        return {"url": url, "success": False, "engine_used": "curl", "reason": f"error: {r['error']}"}
    ok, reason = evaluate_success(r.get("status_code"), r.get("text_sample"), r.get("text_len"))
    return {"url": url, "success": ok, "engine_used": "curl", "reason": reason}


async def main(input_file, output_file):
    with open(input_file, encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Demo-Scraper (3 Stufen: Selenium -> {ENGINE} -> curl) | {len(urls)} URLs")
    print(f"Selenium verfuegbar: {SELENIUM_AVAILABLE}")

    sem = asyncio.Semaphore(CONCURRENCY)
    results_by_url = {}

    async def bounded(url, browser):
        async with sem:
            return await scrape_url(url, browser)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [bounded(u, browser) for u in urls]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            res = await coro
            results_by_url[res["url"]] = res
            if i % 10 == 0:
                print(f"{i}/{len(urls)} verarbeitet...")
        await browser.close()

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "success", "engine_used", "reason"])
        writer.writeheader()
        for url in urls:
            writer.writerow(results_by_url.get(url, {"url": url, "success": False, "engine_used": "none", "reason": "missing"}))

    success = sum(1 for r in results_by_url.values() if r["success"])
    print(f"\nErfolgreich: {success}/{len(urls)} ({success/len(urls)*100:.1f}%)")
    print(Counter(r["engine_used"] for r in results_by_url.values() if r["success"]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Nutzung: python demo_new_scraping.py failed_source.csv results.csv")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
