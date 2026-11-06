"""Lokal E2E: alohida SQLite + uvicorn + Playwright.

Production DB ga tegmaydi. Haqiqiy to'lov/Telegram yuborilmaydi.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E2E = Path(__file__).resolve().parent
WORKDIR = E2E / ".runtime"
DB_PATH = WORKDIR / "e2e.db"
PORT = int(os.environ.get("E2E_PORT", "8020"))
BASE = f"http://127.0.0.1:{PORT}"


def _wait_http(url: str, timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 500:
                    return
                last = f"status={resp.status}"
        except Exception as exc:  # noqa: BLE001 — kutish davri
            last = str(exc)
        time.sleep(0.4)
    raise RuntimeError(f"Server ochilmadi: {url} ({last})")


def main() -> int:
    if WORKDIR.exists():
        shutil.rmtree(WORKDIR, ignore_errors=True)
    WORKDIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["E2E_DATABASE_PATH"] = str(DB_PATH)
    prepare = subprocess.run(
        [sys.executable, str(E2E / "prepare_db.py")],
        cwd=str(ROOT),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if prepare.returncode != 0:
        print(prepare.stdout)
        print(prepare.stderr, file=sys.stderr)
        return prepare.returncode

    db_url = prepare.stdout.strip().splitlines()[-1]
    print(f"E2E DB: {db_url}")

    server_env = os.environ.copy()
    server_env.update(
        {
            "DATABASE_URL": db_url,
            "DEV_MODE": "true",
            "DEBUG": "true",
            "TELEGRAM_WEBAPP_ONLY": "false",
            "QUESTION_VARIANTS": "V2",
            "SECRET_KEY": "e2e-secret-key-not-for-production",
            # E2E premium modalini ochish uchun soxta bot/karta (haqiqiy to'lov yo'q).
            "BOT_USERNAME": "xarakterim_e2e_bot",
            "TELEGRAM_BOT_USERNAME": "xarakterim_e2e_bot",
            "PAYMENT_SUPPORT_BOT_USERNAME": "xarakterim_e2e_bot",
            "PAYMENT_CARD_NUMBER": "8600 0000 0000 0000",
            "PAYMENT_CARD_HOLDER": "E2E TEST",
            "E2E_BASE_URL": BASE,
        }
    )
    # Lokal .env ni bekor qilish: uvicorn jarayonida DATABASE_URL ustun.
    server_log = open(WORKDIR / "uvicorn.log", "w", encoding="utf-8")
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=str(ROOT),
        env=server_env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
    )

    try:
        try:
            _wait_http(f"{BASE}/personality")
        except RuntimeError:
            server_log.flush()
            print((WORKDIR / "uvicorn.log").read_text(encoding="utf-8", errors="replace"))
            raise
        print(f"Server tayyor: {BASE}")

        npm_install = subprocess.run(
            ["npm", "install"],
            cwd=str(E2E),
            check=False,
            shell=True,
        )
        if npm_install.returncode != 0:
            return npm_install.returncode

        browsers = subprocess.run(
            ["npx", "playwright", "install", "chromium"],
            cwd=str(E2E),
            check=False,
            shell=True,
        )
        if browsers.returncode != 0:
            return browsers.returncode

        test_env = os.environ.copy()
        test_env["E2E_BASE_URL"] = BASE
        test_env["E2E_DATABASE_PATH"] = str(DB_PATH)
        result = subprocess.run(
            ["npx", "playwright", "test"],
            cwd=str(E2E),
            env=test_env,
            check=False,
            shell=True,
        )
        return result.returncode
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        server_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
