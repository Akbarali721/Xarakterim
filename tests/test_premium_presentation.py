"""Premium natija 6 bo'limli taqdimot — tip matni + score-based boyitish."""

from types import SimpleNamespace

from app.personality.result_personalization import build_result_profile
from app.seed.personality_results_uz import get_result_copy
from app.services.premium_presentation import compose_premium_blocks


def _content(ptype: str = "ENFP"):
    copy = get_result_copy(ptype)
    return SimpleNamespace(**copy), copy


def _profile(**scores):
    base = {"e": 18, "i": 6, "s": 6, "n": 18, "t": 6, "f": 18, "j": 6, "p": 18}
    base.update(scores)
    return build_result_profile(**base, language="uz")


def test_compose_premium_blocks_returns_six_sections():
    content, copy = _content("INFP")
    blocks = compose_premium_blocks(
        content,
        copy["strengths"],
        copy["challenges"],
        language="uz",
    )
    assert len(blocks) == 6
    assert blocks[0].title_key == "result.premium.brief"
    assert blocks[0].body
    assert blocks[1].title_key == "result.premium.strengths"
    assert len(blocks[1].bullets) == 3
    assert blocks[2].title_key == "result.premium.drains"
    assert len(blocks[2].bullets) >= 2
    assert blocks[3].sub_bullets
    assert blocks[5].bullets


def test_same_type_different_scores_change_premium_blocks():
    """A: bir tip, turli ball — Premium asosli farq qilsin."""
    content, copy = _content("ENFP")
    strong = _profile(e=24, i=4, s=6, n=20, t=6, f=20, j=6, p=20)
    soft = _profile(e=14, i=12, s=10, n=16, t=12, f=14, j=11, p=15)
    left = compose_premium_blocks(
        content, copy["strengths"], copy["challenges"], language="uz", profile=strong
    )
    right = compose_premium_blocks(
        content, copy["strengths"], copy["challenges"], language="uz", profile=soft
    )
    assert left[0].body != right[0].body
    assert left[1].bullets != right[1].bullets


def test_close_ei_softens_premium_and_matches_free():
    """B: E/I yaqin — Premium free o‘qish bilan mos, tip-only dan farq qilsin."""
    content, copy = _content("ENFP")
    profile = _profile(e=13, i=12, s=20, n=6, t=18, f=8, j=18, p=8)
    assert profile["notes"][0]["ambiguous"] is True
    blocks = compose_premium_blocks(
        content, copy["strengths"], copy["challenges"], language="uz", profile=profile
    )
    baseline = compose_premium_blocks(
        content, copy["strengths"], copy["challenges"], language="uz", profile=None
    )
    brief = blocks[0].body or ""
    assert brief != (baseline[0].body or "")
    for part in profile["summary"]:
        assert str(part) in brief
    # Yaqin E/I izohi munosabat bo‘limiga ko‘chadi (free notes bilan bir xil).
    assert str(profile["notes"][0]["body"]) in (blocks[4].body or "")


def test_multi_low_confidence_does_not_firmly_bind_type_strengths():
    """C: bir nechta o'lchovda low-confidence."""
    content, copy = _content("INTJ")
    profile = build_result_profile(
        e=13, i=12, s=13, n=12, t=13, f=12, j=13, p=12, language="uz"
    )
    assert profile["show_type_heading"] is False
    blocks = compose_premium_blocks(
        content, copy["strengths"], copy["challenges"], language="uz", profile=profile
    )
    assert "qat’iy xulosa emas" in (blocks[0].body or "")
    assert len(blocks[1].bullets) == 1
    assert "Aniq ustunlik" in blocks[1].bullets[0] or "kuchli tomon" in blocks[1].bullets[0]
    assert "yumshoq" in " ".join(blocks[5].bullets).lower() or "yaqin" in " ".join(blocks[5].bullets)


def test_without_profile_keeps_type_static_baseline():
    content, copy = _content("INFJ")
    blocks = compose_premium_blocks(
        content, copy["strengths"], copy["challenges"], language="uz", profile=None
    )
    assert blocks[0].body
    assert len(blocks[1].bullets) >= 2
