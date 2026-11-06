"""Preference-based free result copy follows stored scores, not the type essay."""

from app.personality.result_personalization import build_result_profile
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import DIMENSION_POLES
from tests.helpers import complete_session, db_session, session_by_token


def _favor_left(question):
    left, _right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == left else 3


def _favor_right(question):
    _left, right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == right else 3


def _profile(**scores):
    base = {"e": 4, "i": 18, "s": 18, "n": 4, "t": 18, "f": 4, "j": 18, "p": 4}
    base.update(scores)
    return build_result_profile(**base, language="uz")


def test_strong_introversion_and_extraversion_read_differently():
    inward = _profile(e=4, i=18)
    outward = _profile(e=18, i=4)
    assert "o‘zingiz o‘ylab" in inward["summary"][0]
    assert "gaplashib" in outward["summary"][0]
    assert inward["show_type_heading"] is True
    assert "uyatchan" not in " ".join(inward["summary"]).lower()


def test_close_scores_are_not_a_firm_conclusion():
    profile = _profile(s=9, n=7, j=8, p=6)
    text = " ".join(profile["summary"])
    assert profile["notes"][1]["ambiguous"] is True
    assert profile["notes"][3]["ambiguous"] is True
    assert "qat’iy xarakter xulosasi berilmaydi" in text
    assert profile["show_type_heading"] is False


def test_complete_ties_do_not_name_a_winner_or_a_type_heading():
    profile = build_result_profile(
        e=9, i=9, s=9, n=9, t=9, f=9, j=9, p=9, language="uz"
    )
    text = " ".join(profile["summary"])
    assert profile["show_type_heading"] is False
    assert "qat’iy xarakter xulosasi berilmaydi" in text
    assert profile["strengths"] == []
    assert profile["challenges"] == []
    assert "Tugashi:" in profile["today"]
    assert "afzal ko‘rishingiz mumkin" not in text


def test_same_letters_with_different_gaps_do_not_share_one_essay():
    firm = _profile()
    close = build_result_profile(
        e=9, i=7, s=9, n=7, t=9, f=7, j=9, p=7, language="uz"
    )
    assert firm["summary"] != close["summary"]
    assert firm["show_type_heading"] is True
    assert close["show_type_heading"] is False


def test_intent_frames_today_without_inventing_a_goal():
    plain = build_result_profile(
        e=4, i=18, s=18, n=4, t=18, f=4, j=18, p=4, language="uz", intent=None
    )
    career = build_result_profile(
        e=4, i=18, s=18, n=4, t=18, f=4, j=18, p=4, language="uz", intent="career"
    )
    unknown = build_result_profile(
        e=4, i=18, s=18, n=4, t=18, f=4, j=18, p=4, language="uz", intent="startup"
    )
    assert career["today"].startswith("Ish yoki o‘qishdagi")
    assert plain["today"] == unknown["today"]
    assert "startap" not in career["today"].lower()


def test_russian_profile_does_not_fall_back_to_uzbek_sentences():
    profile = build_result_profile(
        e=18, i=4, s=18, n=4, t=18, f=4, j=18, p=4, language="ru"
    )
    text = " ".join(profile["summary"])
    assert "По вашим ответам" in text
    assert "Javoblaringizga" not in text
    assert "Холодно" not in text


def test_clear_and_tied_pages_keep_free_access_and_the_premium_lock(client):
    tied = complete_session(client)
    tied_page = client.get(f"/personality/result/{tied}")
    assert tied_page.status_code == 200
    assert "Javoblaringiz aralash chiqdi" in tied_page.text
    assert "mbti-premium-locked-note" in tied_page.text

    client.cookies.clear()
    clear = complete_session(client, option_picker=_favor_left)
    with db_session(client) as db:
        title = session_by_token(db, clear).result_type
        heading = PersonalityRepository(db).get_result_content(title, "uz").title
    clear_page = client.get(f"/personality/result/{clear}")
    assert heading in clear_page.text
    assert "Javoblaringiz aralash chiqdi" not in clear_page.text
    assert "mbti-premium-locked-note" in clear_page.text

    client.cookies.clear()
    other = complete_session(client, option_picker=_favor_right)
    with db_session(client) as db:
        other_heading = PersonalityRepository(db).get_result_content(
            session_by_token(db, other).result_type, "uz"
        ).title
    other_page = client.get(f"/personality/result/{other}")
    assert other_page.status_code == 200
    assert other_heading in other_page.text
    assert other_heading != heading
    assert "mbti-premium-locked-note" in other_page.text
