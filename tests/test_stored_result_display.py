"""Saqlangan tip ko'rsatishda qayta hisoblanmasligi kerak (teng / yaqin / aniq)."""

from __future__ import annotations

from app.personality.result_personalization import build_result_profile
from app.personality.share_code import share_path
from app.repositories.personality_repository import PersonalityRepository
from app.services.personality_scoring import (
    calculate_personality_result,
    personality_result_from_stored,
)
from app.services.personality_service import PersonalityService
from tests.helpers import (
    complete_session,
    db_session,
    favor_left_option_index,
    session_by_token,
)


def test_from_stored_keeps_letter_that_saltless_calc_would_flip():
    """Bo'sh salt bilan hisob boshqa harf bersa ham, saqlangan tip qoladi."""
    salt = None
    for n in range(64):
        candidate = f"display-fix-salt-{n}"
        with_salt = calculate_personality_result(
            9, 9, 12, 6, 12, 6, 12, 6, tie_salt=candidate
        ).result_type[0]
        no_salt = calculate_personality_result(9, 9, 12, 6, 12, 6, 12, 6).result_type[0]
        if with_salt != no_salt:
            salt = candidate
            break
    assert salt is not None

    stored_letter = calculate_personality_result(
        9, 9, 12, 6, 12, 6, 12, 6, tie_salt=salt
    ).result_type[0]
    display = personality_result_from_stored(
        f"{stored_letter}STJ",
        9,
        9,
        12,
        6,
        12,
        6,
        12,
        6,
        ei_low_confidence=True,
        sn_low_confidence=False,
        tf_low_confidence=False,
        jp_low_confidence=False,
    )
    assert display.result_type[0] == stored_letter
    assert display.ei.low_confidence is True
    assert display.sn.low_confidence is False
    assert display.ei.left_percent + display.ei.right_percent == 100


def test_clear_close_and_tie_views_match_stored_session(client):
    clear_token = complete_session(client, option_picker=favor_left_option_index)
    client.cookies.clear()
    close_token = complete_session(client, option_picker=favor_left_option_index)
    client.cookies.clear()
    tie_token = complete_session(client, option_index=0)

    with db_session(client) as db:
        clear = session_by_token(db, clear_token)
        close = session_by_token(db, close_token)
        tied = session_by_token(db, tie_token)

        service = PersonalityService(db)
        clear_view = service.get_result_view(clear_token)
        assert clear_view["result"].result_type == clear.result_type
        assert clear_view["result"].ei.low_confidence is False

        # Yaqin ball: tip harfi saqlanadi, low-confidence flaglari yangilanadi.
        close.e_score = 9
        close.i_score = 7
        close.s_score = 9
        close.n_score = 7
        close.t_score = 9
        close.f_score = 7
        close.j_score = 9
        close.p_score = 7
        close.ei_low_confidence = True
        close.sn_low_confidence = True
        close.tf_low_confidence = True
        close.jp_low_confidence = True
        stored_close_type = close.result_type
        db.commit()

        close_view = service.get_result_view(close_token)
        tie_view = service.get_result_view(tie_token)

        assert close_view["result"].result_type == stored_close_type
        assert close_view["result"].ei.low_confidence is True
        assert close_view["result"].ei.left_percent != 50
        assert tie_view["result"].result_type == tied.result_type
        assert tie_view["result"].ei.low_confidence is True
        assert tie_view["result"].ei.left_percent == 50

        clear_profile = build_result_profile(
            e=clear.e_score,
            i=clear.i_score,
            s=clear.s_score,
            n=clear.n_score,
            t=clear.t_score,
            f=clear.f_score,
            j=clear.j_score,
            p=clear.p_score,
            language="uz",
        )
        close_profile = build_result_profile(
            e=9, i=7, s=9, n=7, t=9, f=7, j=9, p=7, language="uz"
        )
        tie_profile = build_result_profile(
            e=tied.e_score,
            i=tied.i_score,
            s=tied.s_score,
            n=tied.n_score,
            t=tied.t_score,
            f=tied.f_score,
            j=tied.j_score,
            p=tied.p_score,
            language="uz",
        )
        assert clear_profile["show_type_heading"] is True
        assert close_profile["show_type_heading"] is False
        assert tie_profile["show_type_heading"] is False


def test_result_and_share_show_the_same_stored_type(client):
    token = complete_session(client, option_index=0)
    with db_session(client) as db:
        session = session_by_token(db, token)
        stored_type = session.result_type
        share_code = session.share_code
        assert stored_type and share_code
        content_title = PersonalityRepository(db).get_result_content(stored_type, "uz").title
        view = PersonalityService(db).get_result_view(token)
        assert view["result"].result_type == stored_type
        assert view["content"].title == content_title

    result_page = client.get(f"/personality/result/{token}")
    assert result_page.status_code == 200
    # To'liq tenglikda bepul sahifa tip sarlavhasini yashiradi.
    assert "Javoblaringiz aralash chiqdi" in result_page.text

    share_page = client.get(share_path(share_code))
    assert share_page.status_code == 200
    assert stored_type in share_page.text
    assert content_title in share_page.text


def test_clear_result_page_title_matches_stored_type(client):
    token = complete_session(client, option_picker=favor_left_option_index)
    with db_session(client) as db:
        session = session_by_token(db, token)
        stored_type = session.result_type
        title = PersonalityRepository(db).get_result_content(stored_type, "uz").title
        view_type = PersonalityService(db).get_result_view(token)["result"].result_type
        assert view_type == stored_type
        share_code = session.share_code

    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert title in page.text

    share_page = client.get(share_path(share_code))
    assert share_page.status_code == 200
    assert stored_type in share_page.text
    assert title in share_page.text
