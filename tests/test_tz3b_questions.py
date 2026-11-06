"""TZ-3B: approved question texts, bank pairs, and seed safety."""

from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path

from sqlalchemy import select

from app.models.enums import PersonalityDimension
from app.models.personality import PersonalityAnswer, PersonalityOption, PersonalityQuestion
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import (
    DIMENSION_POLES,
    OPTION_WEIGHTS,
    PERSONALITY_QUESTIONS_BANK,
    _option_scores,
    seed_personality_questions,
)
from app.seed.personality_questions_uz import PERSONALITY_QUESTIONS_UZ
from tests.helpers import db_session, start_session


def _approved_questions():
    path = Path(__file__).resolve().parents[1] / "personality_questions_uz_TZ3B_approved.py"
    spec = importlib.util.spec_from_file_location("tz3b_approved_questions", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PERSONALITY_QUESTIONS_UZ


def test_seed_list_matches_approved_file_exactly():
    approved = _approved_questions()
    assert PERSONALITY_QUESTIONS_UZ == approved
    assert len(PERSONALITY_QUESTIONS_UZ) == 24
    assert sum(len(options) for _text, _dim, options in PERSONALITY_QUESTIONS_UZ) == 96
    assert all(len(options) == 4 for _text, _dim, options in PERSONALITY_QUESTIONS_UZ)

    counts = Counter(dimension for _text, dimension, _options in PERSONALITY_QUESTIONS_UZ)
    assert counts == {
        PersonalityDimension.EI: 6,
        PersonalityDimension.SN: 6,
        PersonalityDimension.TF: 6,
        PersonalityDimension.JP: 6,
    }
    texts = [text for text, _dimension, _options in PERSONALITY_QUESTIONS_UZ]
    assert len(set(texts)) == 24


def test_reversed_bank_keeps_the_same_answer_direction():
    assert len(PERSONALITY_QUESTIONS_BANK) == 48
    assert OPTION_WEIGHTS == (3, 1, 1, 3)

    for index in range(0, 48, 2):
        text, dimension, options, primary = PERSONALITY_QUESTIONS_BANK[index]
        twin_text, twin_dimension, reversed_options, twin_primary = PERSONALITY_QUESTIONS_BANK[index + 1]
        left, right = DIMENSION_POLES[dimension]
        assert twin_text == text
        assert twin_dimension == dimension
        assert primary == left
        assert twin_primary == right
        assert reversed_options == list(reversed(options))

        for option_index, option_text in enumerate(options):
            original_scores = _option_scores(primary, option_index, dimension)
            mirrored_scores = _option_scores(twin_primary, 3 - option_index, dimension)
            assert original_scores == mirrored_scores
            assert reversed_options[3 - option_index] == option_text
            target = left if option_index < 2 else right
            assert original_scores[target] == OPTION_WEIGHTS[option_index]


def test_valid_bank_is_not_rewritten_without_force(client):
    with db_session(client) as db:
        question = db.scalar(
            select(PersonalityQuestion).where(
                PersonalityQuestion.variant == "A",
                PersonalityQuestion.order_number == 1,
            )
        )
        assert question is not None
        option = min(question.options, key=lambda row: row.order_number)
        question.text = "ESKI SAVOL MATNI"
        option.text = "ESKI JAVOB MATNI"
        db.commit()

        added = seed_personality_questions(db, force=False, variant="A")
        db.refresh(question)
        db.refresh(option)
        assert added == 0
        assert question.text == "ESKI SAVOL MATNI"
        assert option.text == "ESKI JAVOB MATNI"


def test_force_seed_would_replace_text_of_an_answered_option(client):
    """Documents the hazard: --force rewrites option text while keeping the same id."""
    with db_session(client) as db:
        question = db.scalar(
            select(PersonalityQuestion).where(
                PersonalityQuestion.variant == "A",
                PersonalityQuestion.order_number == 1,
            )
        )
        assert question is not None
        option = min(question.options, key=lambda row: row.order_number)
        option_id = option.id
        question.text = "ESKI SAVOL MATNI"
        option.text = "ESKI JAVOB MATNI"
        session = PersonalityRepository(db).create_session(source="test")
        db.add(
            PersonalityAnswer(
                session_id=session.id,
                question_id=question.id,
                option_id=option_id,
            )
        )
        db.commit()

        seed_personality_questions(db, force=True, variant="A")
        refreshed = db.get(PersonalityOption, option_id)
        assert refreshed is not None
        assert refreshed.id == option_id
        assert refreshed.text == PERSONALITY_QUESTIONS_UZ[0][2][0]
        assert refreshed.text != "ESKI JAVOB MATNI"
        answer = db.scalar(select(PersonalityAnswer).where(PersonalityAnswer.option_id == option_id))
        assert answer is not None
        assert answer.option_id == refreshed.id


def test_live_question_page_shows_an_approved_answer(client):
    token = start_session(client)
    page = client.get(f"/personality/test/{token}?q=0")
    assert page.status_code == 200
    approved_options = [option for _text, _dim, options in PERSONALITY_QUESTIONS_UZ for option in options]
    assert any(option in page.text for option in approved_options)
    assert "mbti-option-text" in page.text
