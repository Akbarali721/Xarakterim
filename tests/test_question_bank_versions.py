"""V1 stays frozen; new sessions draw only the V2 bank."""

from __future__ import annotations

from sqlalchemy import func, select

from app.config import settings
from app.models.enums import PersonalityDimension
from app.models.personality import (
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityTestSession,
)
from app.personality.constants import (
    QUESTION_BANK_V1,
    QUESTION_BANK_V2,
    QUESTIONS_PER_DIMENSION,
    SESSION_QUESTION_COUNT,
)
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import question_bank_is_valid, seed_v2_question_bank
from tests.helpers import (
    complete_session,
    db_session,
    extract_hidden,
    session_by_token,
    start_session,
)


def _ids(rows: list[PersonalityQuestion]) -> set[int]:
    return {row.id for row in rows}


def _bank(db, variant: str) -> list[PersonalityQuestion]:
    return list(
        db.scalars(
            select(PersonalityQuestion).where(PersonalityQuestion.variant == variant)
        ).all()
    )


def test_v2_reseed_does_not_rewrite_v1_or_duplicate_rows(client):
    with db_session(client) as db:
        v1_before = {
            (row.id, row.text, row.order_number)
            for row in _bank(db, QUESTION_BANK_V1)
        }
        option = db.scalar(
            select(PersonalityOption)
            .join(PersonalityQuestion)
            .where(PersonalityQuestion.variant == QUESTION_BANK_V1)
            .order_by(PersonalityOption.id)
        )
        assert option is not None
        option.text = "V1-JAVOB-SAQLANSIN"
        option_id = option.id
        db.commit()

        v2_ids_before = _ids(_bank(db, QUESTION_BANK_V2))
        assert len(v2_ids_before) == 48
        assert seed_v2_question_bank(db) == 0
        assert seed_v2_question_bank(db) == 0

        v1_after = {
            (row.id, row.text, row.order_number)
            for row in _bank(db, QUESTION_BANK_V1)
        }
        saved = db.get(PersonalityOption, option_id)
        v2_after = _bank(db, QUESTION_BANK_V2)
        assert v1_after == v1_before
        assert saved is not None and saved.text == "V1-JAVOB-SAQLANSIN"
        assert _ids(v2_after) == v2_ids_before
        assert question_bank_is_valid(db, QUESTION_BANK_V2)
        option_count = db.scalar(
            select(func.count())
            .select_from(PersonalityOption)
            .join(PersonalityQuestion)
            .where(PersonalityQuestion.variant == QUESTION_BANK_V2)
        )
        assert option_count == 192


def test_incomplete_v1_session_keeps_its_questions(client, monkeypatch):
    monkeypatch.setattr(settings, "question_variants", QUESTION_BANK_V1)
    token = start_session(client)
    first = client.get(f"/personality/test/{token}?q=0")
    question_id = extract_hidden(first.text, "question_id")

    monkeypatch.setattr(settings, "question_variants", QUESTION_BANK_V2)
    again = client.get(f"/personality/test/{token}?q=0")
    assert extract_hidden(again.text, "question_id") == question_id

    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.variant == QUESTION_BANK_V1
        selected = PersonalityRepository(db).get_session_questions_ordered(session)
        assert len(selected) == SESSION_QUESTION_COUNT
        assert {question.variant for question in selected} == {QUESTION_BANK_V1}


def test_new_session_uses_only_v2_and_can_finish(client, monkeypatch):
    monkeypatch.setattr(settings, "question_variants", QUESTION_BANK_V1)
    v1_token = complete_session(client)
    with db_session(client) as db:
        v1_session = session_by_token(db, v1_token)
        v1_result = v1_session.result_type
        v1_answers = list(
            db.scalars(
                select(PersonalityAnswer).where(PersonalityAnswer.session_id == v1_session.id)
            ).all()
        )
        v1_answer_snapshot = [(row.id, row.option_id, row.question_id) for row in v1_answers]
        assert v1_result and len(v1_result) == 4
        assert len(v1_answer_snapshot) == SESSION_QUESTION_COUNT

    assert client.get(f"/personality/result/{v1_token}").status_code == 200
    monkeypatch.setattr(settings, "question_variants", QUESTION_BANK_V2)
    restarted = client.post("/personality/restart", follow_redirects=False)
    assert restarted.status_code == 303
    v2_token = complete_session(client)

    dimensions = {
        PersonalityDimension.EI,
        PersonalityDimension.SN,
        PersonalityDimension.TF,
        PersonalityDimension.JP,
    }
    with db_session(client) as db:
        v1_session = session_by_token(db, v1_token)
        assert v1_session.result_type == v1_result
        answers_now = [
            (row.id, row.option_id, row.question_id)
            for row in db.scalars(
                select(PersonalityAnswer).where(PersonalityAnswer.session_id == v1_session.id)
            ).all()
        ]
        assert answers_now == v1_answer_snapshot

        v2_session = session_by_token(db, v2_token)
        assert v2_session.variant == QUESTION_BANK_V2
        assert v2_session.result_type and len(v2_session.result_type) == 4
        selected = PersonalityRepository(db).get_session_questions_ordered(v2_session)
        assert len(selected) == SESSION_QUESTION_COUNT
        assert {question.variant for question in selected} == {QUESTION_BANK_V2}
        assert len({question.id for question in selected}) == SESSION_QUESTION_COUNT
        counts: dict[PersonalityDimension, int] = {dimension: 0 for dimension in dimensions}
        for question in selected:
            counts[question.dimension] += 1
        assert set(counts.values()) == {QUESTIONS_PER_DIMENSION}
        for start in range(0, SESSION_QUESTION_COUNT, 4):
            block = selected[start : start + 4]
            assert {question.dimension for question in block} == dimensions

    assert client.get(f"/personality/result/{v1_token}").status_code == 200
    assert client.get(f"/personality/result/{v2_token}").status_code == 200
    assert "Natijangiz qanday shakllandi?" in client.get(f"/personality/result/{v2_token}?lang=uz").text
