"""E2E uchun alohida SQLite baza: V1+V2 savollar va natija matnlari."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.personality.constants import QUESTION_BANK_V1, QUESTION_BANK_V2
from app.seed.personality_placeholders import seed_personality_questions, seed_personality_results


def main() -> None:
    db_path = Path(os.environ["E2E_DATABASE_PATH"]).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        seed_personality_questions(db, variant=QUESTION_BANK_V1)
        seed_personality_questions(db, variant=QUESTION_BANK_V2)
        seed_personality_results(db)
        db.commit()
    finally:
        db.close()
        engine.dispose()

    print(url)


if __name__ == "__main__":
    main()
