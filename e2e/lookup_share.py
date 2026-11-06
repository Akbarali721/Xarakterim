"""Result tokenidan share_code ni E2E SQLite dan o'qiydi."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.personality import PersonalityTestSession


def main() -> None:
    token = sys.argv[1]
    db_path = Path(os.environ["E2E_DATABASE_PATH"]).resolve()
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        row = db.scalar(
            select(PersonalityTestSession).where(PersonalityTestSession.token == token)
        )
        if row is None or not row.share_code:
            raise SystemExit(f"share_code topilmadi: {token}")
        print(row.share_code)
        print(row.result_type or "")
        print(row.variant or "")
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
