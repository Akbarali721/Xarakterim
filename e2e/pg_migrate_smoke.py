"""Lokal Docker PostgreSQL da Alembic + V2 seed smoke.

Faqat localhost/127.0.0.1 hostiga ruxsat. Railway/production URL rad etiladi.
Maxfiy kalitlarni chop etmaydi.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

# Host/port/db ochiq; parol faqat lokal konteyner uchun.
TEST_URL = (
    "postgresql+psycopg2://xarakterim_test:xarakterim_test_only@"
    "127.0.0.1:55432/xarakterim_migrate"
)


def _assert_safe_url(url: str) -> None:
    parsed = urlparse(url.replace("postgresql+psycopg2", "postgresql", 1))
    host = (parsed.hostname or "").lower()
    if host not in {"127.0.0.1", "localhost"}:
        raise SystemExit(f"XAVFSIZLIK: host lokal emas: {host!r}")
    if "railway" in url.lower() or "rlwy" in url.lower():
        raise SystemExit("XAVFSIZLIK: Railway URL aniqlandi")
    if parsed.port not in {55432, 5432, None}:
        # 55432 — bizning test konteyneri; 5432 ham lokal bo'lishi mumkin.
        pass
    print(f"SAFE_URL host={host} port={parsed.port} db={parsed.path.lstrip('/')}")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_URL
    env["SECRET_KEY"] = "migratsiya-testi-uchun-kalit-" + "z" * 24
    env["DEBUG"] = "true"
    env["DEV_MODE"] = "false"
    # Settings importi .env ni o'qishi mumkin — production URL ni bosib o'tamiz.
    return env


def _wait_pg(timeout: float = 60.0) -> None:
    import psycopg2

    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                host="127.0.0.1",
                port=55432,
                user="xarakterim_test",
                password="xarakterim_test_only",
                dbname="xarakterim_migrate",
            )
            conn.close()
            print("POSTGRES_CONNECTION PASS")
            return
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            time.sleep(1)
    raise SystemExit(f"POSTGRES_CONNECTION FAIL: {last}")


def _alembic(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(ROOT),
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def _print_alembic(label: str, proc: subprocess.CompletedProcess[str]) -> None:
    # URL/parol chiqmasin — faqat oxirgi qatorlar.
    out = (proc.stdout or "") + (proc.stderr or "")
    lines = [ln for ln in out.splitlines() if "password" not in ln.lower() and "://" not in ln]
    print(f"--- {label} exit={proc.returncode} ---")
    for ln in lines[-30:]:
        print(ln)


def main() -> int:
    _assert_safe_url(TEST_URL)
    _wait_pg()

    first = _alembic(["upgrade", "head"])
    _print_alembic("upgrade#1", first)
    if first.returncode != 0:
        print("ALEMBIC_UPGRADE FAIL")
        return 1
    print("ALEMBIC_UPGRADE PASS")

    second = _alembic(["upgrade", "head"])
    _print_alembic("upgrade#2", second)
    if second.returncode != 0:
        print("ALEMBIC_SECOND_UPGRADE FAIL")
        return 1
    print("ALEMBIC_SECOND_UPGRADE PASS")

    current = _alembic(["current"])
    heads = _alembic(["heads"])
    _print_alembic("current", current)
    _print_alembic("heads", heads)
    cur_txt = (current.stdout or "") + (current.stderr or "")
    heads_txt = (heads.stdout or "") + (heads.stderr or "")
    # current: "022_result_user_feedback (head)" ; heads: "022_result_user_feedback (head)"
    if "022_result_user_feedback" not in cur_txt or "022_result_user_feedback" not in heads_txt:
        print("CURRENT_VS_HEADS FAIL")
        return 1
    if "(head)" not in cur_txt:
        print("CURRENT_VS_HEADS FAIL (current not at head)")
        return 1
    print("CURRENT_VS_HEADS PASS")

    # Seed V2 + results
    sys.path.insert(0, str(ROOT))
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker

    from app.models.personality import PersonalityQuestion, PersonalityResultContent
    from app.personality.constants import QUESTION_BANK_V1, QUESTION_BANK_V2
    from app.seed.personality_placeholders import (
        seed_personality_questions,
        seed_personality_results,
    )

    engine = create_engine(TEST_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        n1 = seed_personality_questions(db, variant=QUESTION_BANK_V1)
        n2 = seed_personality_questions(db, variant=QUESTION_BANK_V2)
        seed_personality_results(db)
        db.commit()
        v1 = db.scalar(
            select(func.count()).select_from(PersonalityQuestion).where(
                PersonalityQuestion.variant == QUESTION_BANK_V1
            )
        )
        v2 = db.scalar(
            select(func.count()).select_from(PersonalityQuestion).where(
                PersonalityQuestion.variant == QUESTION_BANK_V2
            )
        )
        results = db.scalar(select(func.count()).select_from(PersonalityResultContent))
        print(f"SEED added_v1={n1} added_v2={n2} counts_v1={v1} counts_v2={v2} results={results}")
        if v1 != 48 or v2 != 48 or not results or results < 16:
            print("V2_SEED FAIL")
            return 1
        # Reseed idempotent
        n2b = seed_personality_questions(db, variant=QUESTION_BANK_V2)
        db.commit()
        if n2b != 0:
            print(f"V2_SEED FAIL reseed_added={n2b}")
            return 1
        print("V2_SEED PASS")
    finally:
        db.close()
        engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
