"""
Browser smoke test for the Streamlit UI (Playwright, headless Chromium).

Not collected by pytest. Start the backend and the UI (Streamlit from frontend/, so that
frontend/.streamlit/config.toml is used), then point this script at the UI. PowerShell:

    $env:API_BASE_URL = "http://localhost:8100/api"
    Start-Process .venv\Scripts\python.exe -ArgumentList "-m","uvicorn","backend.main:app","--port","8100" `
        -WindowStyle Hidden -RedirectStandardError be.err.log -RedirectStandardOutput be.out.log
    Start-Process .venv\Scripts\python.exe -ArgumentList "-m","streamlit","run","app.py","--server.port","8601","--server.headless","true" `
        -WorkingDirectory frontend -WindowStyle Hidden -RedirectStandardError fe.err.log -RedirectStandardOutput fe.out.log
    .venv\Scripts\python tests\e2e\ui_smoke.py http://localhost:8601

Send the servers' output to files (as above). The webapp-testing skill's with_server.py pipes it
and never reads the pipe, so a backend that logs a lot blocks mid-request and the upload
appears to hang. Stop both servers afterwards (they keep running).

Checks: fonts load, keyboard focus is visible, reduced motion is honoured, no horizontal
scroll at phone width, a clear error for an unreadable file, and the full
upload -> results (range strips) -> questions -> history flow. Screenshots go to tests/e2e/out/.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
SAMPLE_NAME = "sample_report.txt"
SAMPLE = {  # WBC and Neutrophils are outside their printed ranges
    "name": SAMPLE_NAME,
    "mimeType": "text/plain",
    "buffer": b"Hemoglobin 13.8 g/dL 13.0-17.0\nPCV 42.0 % 40-50\nTotal WBC 16500 cumm 4000-11000 High\nNeutrophils 85 % 50-62 High\n",
}

failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def open_app(browser, **kw):
    page = browser.new_page(**kw)
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_load_state("networkidle")  # dynamic app: wait for JS before inspecting
    page.wait_for_selector("h1:has-text('New analysis')", timeout=20000)
    return page, errors


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # 1. Look and accessibility ------------------------------------------------
    page, errors = open_app(browser, viewport={"width": 1280, "height": 900})
    page.wait_for_function("document.fonts.check('16px \"Atkinson Hyperlegible\"')", timeout=10000)
    check("Atkinson Hyperlegible is the page font", "Atkinson" in page.evaluate("getComputedStyle(document.body).fontFamily"))
    outlines = []
    for _ in range(12):
        page.keyboard.press("Tab")
        outlines.append(page.evaluate("getComputedStyle(document.activeElement).outlineWidth"))
    check("keyboard focus shows a 3px outline", "3px" in outlines, str(set(outlines)))
    page.screenshot(path=str(OUT / "1_upload.png"), full_page=True)
    page.emulate_media(reduced_motion="reduce")
    check("reduced motion disables transitions",
          page.evaluate("getComputedStyle(document.querySelector('button')).transitionProperty") == "none")
    page.set_viewport_size({"width": 390, "height": 800})
    page.wait_for_timeout(600)
    check("no horizontal scroll at 390px", not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"))
    page.close()

    # 2. An unreadable file gets a specific message ---------------------------------
    page, errors = open_app(browser, viewport={"width": 1280, "height": 900})
    page.set_input_files("input[type=file]", files=[{"name": "notes.txt", "mimeType": "text/plain", "buffer": b"hello, no lab values here"}])
    page.click("button:has-text('Analyze report')")
    page.wait_for_selector("text=No blood parameters could be extracted", timeout=60000)
    check("error names the problem", True)
    check("error says how to fix it", page.locator("text=then upload it again").count() == 1)
    page.screenshot(path=str(OUT / "2_error.png"), full_page=True)
    page.close()

    # 3. Full flow ----------------------------------------------------------------
    page, errors = open_app(browser, viewport={"width": 1280, "height": 900})
    page.set_input_files("input[type=file]", files=[SAMPLE])
    page.wait_for_selector(f"text={SAMPLE_NAME} is")
    page.click("button:has-text('Analyze report')")
    try:
        page.wait_for_selector("text=Flagged values", timeout=150000)
    except Exception:
        page.screenshot(path=str(OUT / "timeout.png"), full_page=True)
        print("PAGE TEXT AT TIMEOUT:", page.locator("[data-testid=stMain]").first.inner_text()[:600].replace("\n", " | "))
        raise
    page.wait_for_load_state("networkidle")
    strips = page.locator(".rng")
    check("one range strip per flagged value", strips.count() == 2, f"got {strips.count()}")
    labels = [strips.nth(i).get_attribute("aria-label") or "" for i in range(strips.count())]
    check("strips carry the value, status and range as text",
          any("WBC 16500" in l and "high" in l for l in labels) and all("Normal range" in l for l in labels), str(labels))
    check("headline is a plain sentence", page.locator("text=2 of 4 values fall outside the normal range.").count() == 1)
    check("interpretation prose is capped near 68ch",
          page.evaluate("Math.max(...[...document.querySelectorAll('[data-testid=stMarkdownContainer] p')].map(e => e.getBoundingClientRect().width)) < 68 * 12"))
    page.screenshot(path=str(OUT / "3_results.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 800})
    page.wait_for_timeout(600)
    check("results have no horizontal scroll at 390px", not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"))
    page.screenshot(path=str(OUT / "3_results_mobile.png"), full_page=True)
    page.set_viewport_size({"width": 1280, "height": 900})

    page.click("[data-testid=stSidebarNav] a:has-text('Questions')")
    page.wait_for_selector("text=Answering questions about")
    check("questions page shows the open report", page.locator(f"text={SAMPLE_NAME}").count() >= 1)
    page.screenshot(path=str(OUT / "4_questions.png"), full_page=True)

    page.click("[data-testid=stSidebarNav] a:has-text('History')")
    page.wait_for_selector("h1:has-text('History')")
    page.wait_for_selector("text=Analyzed on", timeout=20000)
    check("history lists the report as divided rows", page.locator("button:has-text('Open report')").count() >= 1)
    page.screenshot(path=str(OUT / "5_history.png"), full_page=True)

    check("no console errors during the flow", not errors, str(errors[:3]))
    page.close()
    browser.close()

print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
sys.exit(1 if failures else 0)
