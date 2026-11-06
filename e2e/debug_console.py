"""Natija sahifasidagi pageerror manbasini ko'rsatadi."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E2E = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

DB = E2E / ".runtime" / "debug.db"
PORT = 8011
BASE = f"http://127.0.0.1:{PORT}"


def main() -> None:
    os.environ["E2E_DATABASE_PATH"] = str(DB)
    subprocess.run([sys.executable, str(E2E / "prepare_db.py")], cwd=ROOT, check=True, env={**os.environ})
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{DB.resolve().as_posix()}",
        "DEV_MODE": "true",
        "TELEGRAM_WEBAPP_ONLY": "false",
        "QUESTION_VARIANTS": "V2",
        "SECRET_KEY": "e2e-debug",
    }
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{BASE}/personality", timeout=1)
                break
            except Exception:
                time.sleep(0.3)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda err: print("PAGEERROR:", err, getattr(err, "stack", None)))
            page.on("console", lambda m: print("CONSOLE", m.type, m.text) if m.type == "error" else None)
            page.goto(f"{BASE}/personality")
            page.locator('form[action="/personality/begin"] button').click()
            page.locator("#start-btn").click()
            page.locator('input[name="intent"][value="curiosity"]').check(force=True)
            page.locator(".mbti-intent-submit").click()
            for i in range(24):
                page.locator("label.mbti-option").first.click()
                page.locator("#next-question-button").click()
            page.wait_for_url("**/personality/result/**", timeout=60000)
            if "/loading" in page.url:
                page.wait_for_url("**/personality/result/**", timeout=60000)
            page.wait_for_timeout(2000)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
