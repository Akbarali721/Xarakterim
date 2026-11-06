"""Premium shaxsiylashtirish: locked/unlocked, PDF mosligi, A/V2 sessiyalar."""

from sqlalchemy import select

from app.i18n import t
from app.models.personality import PersonalityAnswer
from app.personality.constants import QUESTION_BANK_V1, QUESTION_BANK_V2
from app.personality.result_personalization import build_result_profile
from app.services.personality_service import PersonalityService
from app.services.premium_payment_service import PremiumPaymentService
from app.services.premium_presentation import compose_premium_blocks
from app.services.premium_report import build_premium_report
from app.services.result_pdf import build_report
from tests.helpers import complete_session, db_session, session_by_token


def _grant_premium(client, token: str) -> None:
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.is_premium = True
        db.commit()


def test_locked_premium_shows_teasers_not_full_bodies(client):
    """D: Premium ochilmagan — teaser, to‘liq blok matni yo‘q."""
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert "is-locked" in page.text
    assert t("result.premium.brief.teaser", "uz") in page.text
    assert t("result.locked_note", "uz") in page.text
    # Soft type note faqat ochilgan Premiumda; locked HTML da to‘liq brief yo‘q.
    assert t("result.premium.soft_type_note", "uz") not in page.text


def test_approved_premium_renders_score_enriched_blocks(client):
    """E: Premium tasdiqlangan — ballarga boyitilgan bloklar ochiq."""
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
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
        payment = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=4242,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        assert PremiumPaymentService(db).approve_payment(payment.id, approved_by="test").code == "approved"

    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert "is-locked" not in page.text
    assert t("result.premium_opened", "uz") in page.text or t("result.premium.brief", "uz") in page.text
    for part in profile["summary"][:1]:
        assert str(part) in page.text


def test_premium_pdf_blocks_match_html_composition(client):
    """F: PDF kontenti HTML compose_premium_blocks bilan mos."""
    token = complete_session(client)
    _grant_premium(client, token)
    with db_session(client) as db:
        session = session_by_token(db, token)
        report = build_premium_report(db, session, language="uz")
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
        view = PersonalityService(db).get_result_view(token, language="uz")
        expected = compose_premium_blocks(
            view["content"],
            list(report.strengths),
            list(report.challenges),
            language="uz",
            profile=profile,
        )
        assert [b.title_key for b in report.blocks] == [b.title_key for b in expected]
        assert report.blocks[0].body == expected[0].body
        assert report.blocks[1].bullets == expected[1].bullets
        pdf_model = build_report(db, token, lang="uz", base_url="http://test")
        assert pdf_model.sections
        assert expected[0].title in {section.title for section in pdf_model.sections}


def test_legacy_a_variant_session_still_personalizes_premium(client, monkeypatch):
    """G: eski A variant sessiyasi Premium boyitishni oladi."""
    from app.config import settings

    monkeypatch.setattr(settings, "question_variants", QUESTION_BANK_V1)
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.variant == QUESTION_BANK_V1
        session.is_premium = True
        db.commit()
        report = build_premium_report(db, session, language="uz")
    assert len(report.blocks) == 6
    assert report.blocks[0].body
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert t("result.premium.brief", "uz") in page.text


def test_v2_variant_session_premium_personalization(client, monkeypatch):
    """H: yangi V2 sessiya Premium ochilganda ballarga asoslanadi."""
    from app.config import settings

    monkeypatch.setattr(settings, "question_variants", QUESTION_BANK_V2)
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.variant == QUESTION_BANK_V2
        answers = list(
            db.scalars(select(PersonalityAnswer).where(PersonalityAnswer.session_id == session.id)).all()
        )
        assert answers
        session.is_premium = True
        # Ballarni aniq ustunlikka suramiz — tip o‘zgarmasa ham brief boyisin.
        session.e_score = 24
        session.i_score = 4
        session.s_score = 6
        session.n_score = 20
        session.t_score = 6
        session.f_score = 20
        session.j_score = 6
        session.p_score = 20
        session.ei_low_confidence = False
        session.sn_low_confidence = False
        session.tf_low_confidence = False
        session.jp_low_confidence = False
        db.commit()
        report = build_premium_report(db, session, language="uz")

    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert "is-locked" not in page.text
    assert report.blocks[0].body
    assert "gaplashib" in (report.blocks[0].body or "") or "Javoblaringiz" in (report.blocks[0].body or "")
