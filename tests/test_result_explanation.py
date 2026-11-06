"""Dimension notes follow stored scores and stay in the active language."""

import random
from types import SimpleNamespace

from app.i18n import t
from app.models.enums import PersonalityDimension
from app.personality.question_selection import _order_in_balanced_blocks
from app.personality.result_explanation import explain_dimensions
from tests.helpers import complete_session


def test_tie_is_described_as_ambiguous_and_a_clear_side_is_not():
    notes = explain_dimensions(e=6, i=6, s=12, n=4, t=12, f=4, j=12, p=4, language="uz")
    assert notes[0]["ambiguous"] is True
    assert notes[0]["body"] == t("result.formed.ei.tie", "uz")
    assert notes[0]["title"] == t("result.formed.ei.title", "uz")
    assert notes[1]["ambiguous"] is False
    assert notes[1]["body"] == t("result.formed.sn.s", "uz")


def test_close_score_names_the_lean_without_a_firm_conclusion():
    notes = explain_dimensions(e=8, i=6, s=6, n=6, t=10, f=4, j=4, p=9, language="ru")
    assert notes[0]["ambiguous"] is True
    assert notes[0]["body"] == t("result.formed.ei.close_e", "ru")
    assert notes[1]["body"] == t("result.formed.sn.tie", "ru")
    assert notes[2]["body"] == t("result.formed.tf.t", "ru")
    assert notes[3]["body"] == t("result.formed.jp.p", "ru")
    assert "qat" not in notes[0]["body"]


def test_result_page_shows_the_explanation_in_both_languages(client):
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert t("result.formed.title", "uz") in page.text
    assert t("result.formed.ei.title", "uz") in page.text
    assert t("result.try_today", "uz") in page.text
    assert t("result.strengths", "uz") in page.text
    assert "mbti-premium-locked-note" in page.text

    russian = client.get(f"/personality/result/{token}?lang=ru")
    assert russian.status_code == 200
    assert t("result.formed.title", "ru") in russian.text
    assert t("result.formed.title", "uz") not in russian.text
    assert t("result.formed.ei.title", "ru") in russian.text
    assert t("result.daily_tips", "ru") in russian.text


def test_dimension_order_inside_each_block_is_shuffled():
    questions = [
        SimpleNamespace(dimension=dimension, marker=index)
        for dimension in (
            PersonalityDimension.EI,
            PersonalityDimension.SN,
            PersonalityDimension.TF,
            PersonalityDimension.JP,
        )
        for index in range(6)
    ]
    first_blocks = set()
    for seed in range(24):
        ordered = _order_in_balanced_blocks(questions, rng=random.Random(seed))
        assert len(ordered) == 24
        assert len({(item.dimension, item.marker) for item in ordered}) == 24
        for start in range(0, 24, 4):
            block = ordered[start : start + 4]
            assert {item.dimension for item in block} == {
                PersonalityDimension.EI,
                PersonalityDimension.SN,
                PersonalityDimension.TF,
                PersonalityDimension.JP,
            }
        first_blocks.add(tuple(item.dimension for item in ordered[:4]))
    assert len(first_blocks) > 1
