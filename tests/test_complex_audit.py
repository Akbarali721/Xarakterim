"""Kompleks audit: savol yuklash, ball, chegaralar, natija mosligi, API xatolari.

Biznes logika o'zgartirilmaydi. Faqat mavjud xatti-harakatni qayd etadi.
"""

from __future__ import annotations

from collections import Counter

from app.models.enums import PersonalityDimension
from app.personality.constants import (
    DIMENSION_LOW_CONFIDENCE_MAX_GAP,
    QUESTION_BANK_V2,
    QUESTIONS_PER_DIMENSION,
    SESSION_QUESTION_COUNT,
)
from app.personality.question_selection import ensure_session_questions
from app.personality.result_personalization import build_result_profile
from app.personality.session_binding import make_result_access_token
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import DIMENSION_POLES, OPTION_WEIGHTS
from app.services.personality_scoring import calculate_personality_result
from tests.helpers import (
    answer_question,
    complete_session,
    db_session,
    extract_hidden,
    favor_left_option_index,
    favor_right_option_index,
    option_ids,
    session_by_token,
    start_session,
)


# ---------------------------------------------------------------------------
# 1. Savollar qanday yuklanadi
# ---------------------------------------------------------------------------


def test_new_session_loads_exactly_24_v2_questions_balanced(client):
    token = start_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        questions = ensure_session_questions(db, session)
        assert session.variant == QUESTION_BANK_V2
        assert len(questions) == SESSION_QUESTION_COUNT
        assert all(q.variant == QUESTION_BANK_V2 for q in questions)
        by_dim = Counter(q.dimension for q in questions)
        assert by_dim == {
            PersonalityDimension.EI: QUESTIONS_PER_DIMENSION,
            PersonalityDimension.SN: QUESTIONS_PER_DIMENSION,
            PersonalityDimension.TF: QUESTIONS_PER_DIMENSION,
            PersonalityDimension.JP: QUESTIONS_PER_DIMENSION,
        }
        poles = Counter()
        for question in questions:
            left, _right = DIMENSION_POLES[question.dimension]
            side = "left" if question.primary_pole == left else "right"
            poles[(question.dimension, side)] += 1
        for dimension in PersonalityDimension:
            assert poles[(dimension, "left")] == 3
            assert poles[(dimension, "right")] == 3


def test_persisted_question_order_does_not_redraw(client):
    token = start_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        first = [q.id for q in ensure_session_questions(db, session)]
        second = [q.id for q in ensure_session_questions(db, session)]
        assert first == second
        assert len(set(first)) == SESSION_QUESTION_COUNT


# ---------------------------------------------------------------------------
# 2–3. Ball algoritmi va chegaralar
# ---------------------------------------------------------------------------


def test_option_weights_are_3_1_1_3():
    assert OPTION_WEIGHTS == (3, 1, 1, 3)


def test_gap_boundary_low_confidence_threshold():
    assert DIMENSION_LOW_CONFIDENCE_MAX_GAP == 2
    at_boundary = calculate_personality_result(8, 6, 12, 4, 12, 4, 12, 4, tie_salt="b")
    just_clear = calculate_personality_result(9, 6, 12, 4, 12, 4, 12, 4, tie_salt="b")
    assert at_boundary.ei.low_confidence is True
    assert just_clear.ei.low_confidence is False
    assert at_boundary.result_type[0] == "E"
    assert just_clear.result_type[0] == "E"


def test_exact_tie_always_low_confidence_and_stable_for_same_salt():
    a = calculate_personality_result(9, 9, 12, 4, 12, 4, 12, 4, tie_salt="same-token")
    b = calculate_personality_result(9, 9, 12, 4, 12, 4, 12, 4, tie_salt="same-token")
    assert a.ei.low_confidence is True
    assert a.result_type[0] == b.result_type[0]


def test_all_first_options_produce_dimension_ties(client):
    """Har savolda A (index 0): 3 chap + 3 o‘ng qutb → har yo‘nalish 9 vs 9."""
    token = complete_session(client, option_index=0)
    with db_session(client) as db:
        session = session_by_token(db, token)
        for left, right in (("e", "i"), ("s", "n"), ("t", "f"), ("j", "p")):
            assert getattr(session, f"{left}_score") == 9
            assert getattr(session, f"{right}_score") == 9
        assert session.ei_low_confidence is True
        assert session.sn_low_confidence is True
        assert session.tf_low_confidence is True
        assert session.jp_low_confidence is True


def test_clear_left_path_scores_match_stored_type(client):
    token = complete_session(client, option_picker=favor_left_option_index)
    with db_session(client) as db:
        session = session_by_token(db, token)
        totals, strong, weak, count = PersonalityRepository(db).score_breakdown_for_session(
            session.id
        )
        assert count == SESSION_QUESTION_COUNT
        recomputed = calculate_personality_result(
            **totals,
            strong_e=strong["e"],
            strong_i=strong["i"],
            strong_s=strong["s"],
            strong_n=strong["n"],
            strong_t=strong["t"],
            strong_f=strong["f"],
            strong_j=strong["j"],
            strong_p=strong["p"],
            weak_e=weak["e"],
            weak_i=weak["i"],
            weak_s=weak["s"],
            weak_n=weak["n"],
            weak_t=weak["t"],
            weak_f=weak["f"],
            weak_j=weak["j"],
            weak_p=weak["p"],
            tie_salt=session.token,
        )
        assert session.result_type == recomputed.result_type
        assert session.e_score > session.i_score
        assert session.s_score > session.n_score
        assert session.t_score > session.f_score
        assert session.j_score > session.p_score
        assert not any(
            [
                session.ei_low_confidence,
                session.sn_low_confidence,
                session.tf_low_confidence,
                session.jp_low_confidence,
            ]
        )


# ---------------------------------------------------------------------------
# 4. Natija generatsiyasi javoblarga mosligi
# ---------------------------------------------------------------------------


def test_free_profile_follows_stored_scores_not_letter_alone(client):
    firm = complete_session(client, option_picker=favor_left_option_index)
    with db_session(client) as db:
        session = session_by_token(db, firm)
        profile = build_result_profile(
            e=session.e_score,
            i=session.i_score,
            s=session.s_score,
            n=session.n_score,
            t=session.t_score,
            f=session.f_score,
            j=session.j_score,
            p=session.p_score,
            language="uz",
            intent=session.intent,
        )
        assert profile["show_type_heading"] is True
        text = " ".join(profile["summary"])
        assert "gaplashib" in text or "afzal ko‘rishingiz mumkin" in text
        assert len(profile["strengths"]) <= 3
        assert len(profile["challenges"]) <= 2
        assert "Tugashi:" in profile["today"]

    client.cookies.clear()
    tied = complete_session(client, option_index=0)
    with db_session(client) as db:
        session = session_by_token(db, tied)
        profile = build_result_profile(
            e=session.e_score,
            i=session.i_score,
            s=session.s_score,
            n=session.n_score,
            t=session.t_score,
            f=session.f_score,
            j=session.j_score,
            p=session.p_score,
            language="uz",
        )
        assert profile["show_type_heading"] is False
        assert "qat’iy xarakter xulosasi berilmaydi" in " ".join(profile["summary"])
        assert profile["strengths"] == []
        assert profile["challenges"] == []


def test_close_gap_personalization_is_not_overconfident():
    profile = build_result_profile(
        e=9, i=7, s=9, n=7, t=18, f=4, j=18, p=4, language="uz"
    )
    assert profile["show_type_heading"] is False
    assert "qat’iy xarakter xulosasi berilmaydi" in " ".join(profile["summary"])
    # Faqat aniq (gap>2) yo‘nalishlar kuchli tomon sifatida chiqadi.
    assert all("title" in item for item in profile["strengths"])
    assert len(profile["strengths"]) == 2


def test_opposite_answers_flip_free_summary(client):
    left = complete_session(client, option_picker=favor_left_option_index)
    client.cookies.clear()
    right = complete_session(client, option_picker=favor_right_option_index)
    with db_session(client) as db:
        a = session_by_token(db, left)
        b = session_by_token(db, right)
        pa = build_result_profile(
            e=a.e_score, i=a.i_score, s=a.s_score, n=a.n_score,
            t=a.t_score, f=a.f_score, j=a.j_score, p=a.p_score, language="uz",
        )
        pb = build_result_profile(
            e=b.e_score, i=b.i_score, s=b.s_score, n=b.n_score,
            t=b.t_score, f=b.f_score, j=b.j_score, p=b.p_score, language="uz",
        )
    assert pa["summary"] != pb["summary"]
    assert a.result_type != b.result_type


# ---------------------------------------------------------------------------
# 5. Ko'rsatish saqlangan tipni qayta hisoblamaydi
# ---------------------------------------------------------------------------


def test_get_result_view_keeps_stored_type_on_full_ties(client):
    from app.services.personality_scoring import personality_result_from_stored
    from app.services.personality_service import PersonalityService

    token = complete_session(client, option_index=0)
    with db_session(client) as db:
        session = session_by_token(db, token)
        view = PersonalityService(db).get_result_view(token)
        rebuilt = personality_result_from_stored(
            session.result_type,
            session.e_score,
            session.i_score,
            session.s_score,
            session.n_score,
            session.t_score,
            session.f_score,
            session.j_score,
            session.p_score,
            ei_low_confidence=session.ei_low_confidence,
            sn_low_confidence=session.sn_low_confidence,
            tf_low_confidence=session.tf_low_confidence,
            jp_low_confidence=session.jp_low_confidence,
        )
        assert view["result"].result_type == session.result_type == rebuilt.result_type
        assert view["result"].ei.low_confidence is True
        assert view["result"].ei.left_percent == 50


# ---------------------------------------------------------------------------
# 6. API / DB xatolari
# ---------------------------------------------------------------------------


def test_unknown_result_token_is_redirected_away(client):
    """Noma'lum token egalik tekshiruvidan o'tmaydi — landingga 303."""
    response = client.get(
        "/personality/result/does-not-exist-token", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/personality"


def test_incomplete_session_cannot_open_result(client):
    token = start_session(client)
    response = client.get(f"/personality/result/{token}", follow_redirects=False)
    assert response.status_code == 303
    assert "/personality/result/" not in response.headers["location"]


def test_answer_rejects_foreign_option(client):
    token = start_session(client)
    page = client.get(f"/personality/test/{token}?q=0")
    question_id = extract_hidden(page.text, "question_id")
    with db_session(client) as db:
        session = session_by_token(db, token)
        questions = ensure_session_questions(db, session)
        other = questions[1]
        foreign_option = sorted(other.options, key=lambda row: row.order_number)[0].id
    posted = client.post(
        f"/personality/test/{token}/answer",
        data={
            "question_id": str(question_id),
            "option_id": str(foreign_option),
            "question_index": "0",
        },
        follow_redirects=False,
    )
    assert posted.status_code == 400


def test_answer_rejects_wrong_question_order(client):
    token = start_session(client)
    page = client.get(f"/personality/test/{token}?q=0")
    question_id = extract_hidden(page.text, "question_id")
    option_id = option_ids(page.text)[0]
    posted = client.post(
        f"/personality/test/{token}/answer",
        data={
            "question_id": str(question_id),
            "option_id": str(option_id),
            "question_index": "3",
        },
        follow_redirects=False,
    )
    assert posted.status_code == 400


def test_answer_rejects_question_not_in_session(client):
    token = start_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        selected_ids = {q.id for q in ensure_session_questions(db, session)}
        outsider = next(
            q
            for q in PersonalityRepository(db).get_active_questions_ordered(
                variant=session.variant
            )
            if q.id not in selected_ids
        )
        option_id = sorted(outsider.options, key=lambda row: row.order_number)[0].id
    posted = client.post(
        f"/personality/test/{token}/answer",
        data={
            "question_id": str(outsider.id),
            "option_id": str(option_id),
            "question_index": "0",
        },
        follow_redirects=False,
    )
    assert posted.status_code == 400


def test_completed_session_answer_redirects_to_result(client):
    token = complete_session(client, option_picker=favor_left_option_index)
    posted = client.post(
        f"/personality/test/{token}/answer",
        data={"question_id": "1", "option_id": "1", "question_index": "0"},
        follow_redirects=False,
    )
    assert posted.status_code == 303
    assert f"/personality/result/{token}" in posted.headers["location"]


def test_free_result_stays_readable_with_access_token(client):
    token = complete_session(client, option_picker=favor_left_option_index)
    client.cookies.clear()
    locked = client.get(f"/personality/result/{token}", follow_redirects=False)
    assert locked.status_code == 303
    opened = client.get(
        f"/personality/result/{token}?access={make_result_access_token(token)}"
    )
    assert opened.status_code == 200
    assert "mbti-result-page" in opened.text
    assert "mbti-premium-locked-note" in opened.text


def test_mid_test_answer_count_matches_progress(client):
    token = start_session(client)
    for index in range(5):
        location = answer_question(client, token, index, option_index=0)
        assert f"q={index + 1}" in location or location.endswith("/loading")
    with db_session(client) as db:
        session = session_by_token(db, token)
        answers = PersonalityRepository(db).score_breakdown_for_session(session.id)[3]
        assert answers == 5
        assert session.status.name != "COMPLETED"
