"""Premium natijani 6 ta qisqa, amaliy bo'limga yig'ish (DB o'zgarmaydi).

Tipga bog'liq matn saqlanadi. Saqlangan E/I–J/P ballari (build_result_profile)
bilan boyitiladi: aniq ustunlikda score-based qatorlar ustun, yaqin/teng
o'lchovlarda qat'iy tip xulosasi yumshatiladi — free natija bilan zid kelmasin.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from app.i18n import t
from app.models.personality import PersonalityResultContent

MAX_WORDS_BODY = 90
MAX_WORDS_PARAGRAPH = 55
STRENGTH_COUNT = 3
DRAIN_COUNT = 3
ACTION_COUNT = 7
MAX_CAREER_EXAMPLES = 6


@dataclass(frozen=True)
class PremiumBlock:
    title_key: str
    title: str
    body: str | None = None
    bullets: tuple[str, ...] = ()
    sub_bullets: tuple[str, ...] = ()


def _words(text: str) -> list[str]:
    return re.findall(r"\S+", (text or "").strip())


def trim_words(text: str, limit: int = MAX_WORDS_BODY) -> str:
    parts = _words(text)
    if len(parts) <= limit:
        return " ".join(parts)
    return " ".join(parts[:limit]).rstrip(".,;:") + "…"


def first_sentences(text: str, count: int = 2) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    chunks = re.split(r"(?<=[.!?])\s+", cleaned)
    chosen = [c for c in chunks if c][:count]
    return " ".join(chosen)


def _lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _brief_summary(content: PersonalityResultContent) -> str:
    """Premium qisqa tavsif bepul «Siz qanday odamsiz?» matnini qaytarmaydi."""
    source = (content.motivation_analysis or "").strip()
    if len(_words(source)) < 20:
        extra = first_sentences(content.public_view or "", 1)
        source = " ".join(part for part in (source, extra) if part)
    return trim_words(source, MAX_WORDS_BODY)


def _strength_bullets(content: PersonalityResultContent, strengths: list[str]) -> tuple[str, ...]:
    """Uch qatorli public_view — kuchli tomonni qayerda ishlatish. Aks holda bepul ro‘yxat."""
    lines = _lines(content.public_view or "")
    if len(lines) >= STRENGTH_COUNT:
        return tuple(trim_words(line, 32) for line in lines[:STRENGTH_COUNT])
    return tuple(trim_words(item, 22) for item in strengths[:STRENGTH_COUNT])


def _drain_bullets(content: PersonalityResultContent, challenges: list[str]) -> tuple[str, ...]:
    """Uch qatorli difficult_communication — vaziyat va yechim. Aks holda qiyinchiliklar."""
    lines = _lines(content.difficult_communication or "")
    if len(lines) >= DRAIN_COUNT:
        return tuple(trim_words(line, 40) for line in lines[:DRAIN_COUNT])
    items = [trim_words(item, 28) for item in challenges[:DRAIN_COUNT]]
    if len(items) < 2 and content.difficult_communication:
        items.append(trim_words(first_sentences(content.difficult_communication, 1), 28))
    return tuple(items[:DRAIN_COUNT])


def _career_example_bullets(career: str) -> tuple[str, ...]:
    text = (career or "").strip()
    if not text:
        return ()
    tail = text.split(":", 1)[-1] if ":" in text else text
    tail = tail.split(".")[0]
    raw = re.split(r"[,;]| va ", tail)
    bullets = [trim_words(part, 8) for part in raw if part.strip()]
    bullets = [b for b in bullets if len(b) > 2]
    return tuple(bullets[:MAX_CAREER_EXAMPLES])


def _relationship_body(content: PersonalityResultContent) -> str:
    chunks = [
        trim_words(first_sentences(content.friendship_style or "", 2), MAX_WORDS_PARAGRAPH),
        trim_words(first_sentences(content.relationship_needs or "", 2), MAX_WORDS_PARAGRAPH),
        trim_words(first_sentences(content.compatible_people or "", 2), MAX_WORDS_PARAGRAPH),
    ]
    unique: list[str] = []
    for chunk in chunks:
        if chunk and chunk not in unique:
            unique.append(chunk)
    return "\n\n".join(unique[:3])


def _action_bullets(plan: str) -> tuple[str, ...]:
    text = (plan or "").strip()
    if not text:
        return ()
    parts = re.split(r"(?<=\.)\s+(?=\d+-kun:)", text)
    if len(parts) > 1:
        cleaned = [trim_words(p.strip().rstrip("."), 28) for p in parts if p.strip()]
        return tuple(cleaned[:ACTION_COUNT])
    parts = re.split(r"(?<=\.)\s+(?=\d+[-–]?(?:kun|hafta|Kun|Hafta))", text)
    if len(parts) <= 1:
        parts = re.split(r"\.\s+(?=[A-ZА-Я0-9«\"'])", text)
    if len(parts) <= 1:
        parts = re.split(r"\.\s+", text)
    cleaned = [trim_words(p.strip().rstrip("."), 28) for p in parts if p.strip()]
    if not cleaned:
        cleaned = [trim_words(text, 28)]
    return tuple(cleaned[:ACTION_COUNT])


def _firm_type_ok(profile: Mapping[str, Any] | None) -> bool:
    """Free bilan bir xil: 2+ noaniq o‘lchovda tipga qat’iy bog‘lanmaymiz."""
    if profile is None:
        return True
    return bool(profile.get("show_type_heading", True))


def _join_paragraphs(*parts: str) -> str:
    return "\n\n".join(p for p in parts if p and p.strip())


def _score_strength_bullets(profile: Mapping[str, Any]) -> tuple[str, ...]:
    items: list[str] = []
    for entry in profile.get("strengths") or []:
        if not isinstance(entry, Mapping):
            continue
        title = str(entry.get("title") or "").strip()
        helps = str(entry.get("helps") or entry.get("meaning") or "").strip()
        line = f"{title}. {helps}".strip(". ").strip() if title else helps
        if line:
            items.append(trim_words(line, 40))
        if len(items) >= STRENGTH_COUNT:
            break
    return tuple(items)


def _score_drain_bullets(profile: Mapping[str, Any]) -> tuple[str, ...]:
    items: list[str] = []
    for entry in profile.get("challenges") or []:
        if not isinstance(entry, Mapping):
            continue
        lead = str(entry.get("lead") or "").strip()
        response = str(entry.get("response") or "").strip()
        line = " ".join(part for part in (lead, response) if part)
        if line:
            items.append(trim_words(line, 40))
        if len(items) >= DRAIN_COUNT:
            break
    return tuple(items)


def _merge_unique(primary: tuple[str, ...], secondary: tuple[str, ...], *, limit: int) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in (*primary, *secondary):
        key = item.casefold()
        if not item or key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= limit:
            break
    return tuple(merged)


def _personalized_brief(
    content: PersonalityResultContent,
    profile: Mapping[str, Any] | None,
    lang: str,
) -> str:
    type_brief = _brief_summary(content)
    if profile is None:
        return type_brief

    summary_parts = [str(p).strip() for p in (profile.get("summary") or []) if str(p).strip()]
    score_text = " ".join(summary_parts)

    if not _firm_type_ok(profile):
        soft = t("result.premium.soft_type_note", lang)
        extra = ""
        if type_brief:
            extra = _join_paragraphs(t("result.premium.type_extra", lang), trim_words(type_brief, 45))
        return trim_words(_join_paragraphs(soft, score_text, extra), MAX_WORDS_BODY + 40)

    if score_text and type_brief:
        return trim_words(_join_paragraphs(score_text, type_brief), MAX_WORDS_BODY + 20)
    return trim_words(score_text or type_brief, MAX_WORDS_BODY)


def _personalized_strengths(
    content: PersonalityResultContent,
    strengths: list[str],
    profile: Mapping[str, Any] | None,
    lang: str,
) -> tuple[str, ...]:
    type_bullets = _strength_bullets(content, strengths)
    if profile is None:
        return type_bullets

    scored = _score_strength_bullets(profile)
    if scored:
        return _merge_unique(scored, type_bullets if _firm_type_ok(profile) else (), limit=STRENGTH_COUNT)

    note = str(profile.get("strength_note") or "").strip() or t("result.premium.no_clear_strength", lang)
    if not _firm_type_ok(profile):
        return (note,)
    return _merge_unique((note,), type_bullets, limit=STRENGTH_COUNT)


def _personalized_drains(
    content: PersonalityResultContent,
    challenges: list[str],
    profile: Mapping[str, Any] | None,
    lang: str,
) -> tuple[str, ...]:
    type_bullets = _drain_bullets(content, challenges)
    if profile is None:
        return type_bullets

    scored = _score_drain_bullets(profile)
    if scored:
        return _merge_unique(scored, type_bullets if _firm_type_ok(profile) else (), limit=DRAIN_COUNT)

    note = str(profile.get("challenge_note") or "").strip() or t("result.premium.no_clear_drain", lang)
    if not _firm_type_ok(profile):
        return (note,)
    return _merge_unique((note,), type_bullets, limit=DRAIN_COUNT)


def _personalized_work(
    content: PersonalityResultContent,
    profile: Mapping[str, Any] | None,
    lang: str,
) -> tuple[str, tuple[str, ...]]:
    career_examples = _career_example_bullets(content.career_environment or "")
    work_intro = trim_words(first_sentences(content.work_style or "", 3), MAX_WORDS_BODY)
    if profile is None:
        return work_intro, career_examples

    tips = [str(tip).strip() for tip in (profile.get("tips") or []) if str(tip).strip()]
    tip_line = tips[0] if tips else ""

    if not _firm_type_ok(profile):
        soft = t("result.premium.soft_type_note", lang)
        body = _join_paragraphs(soft, tip_line, trim_words(work_intro, 50) if work_intro else "")
        return trim_words(body, MAX_WORDS_BODY + 30), career_examples

    if tip_line and work_intro:
        return trim_words(_join_paragraphs(tip_line, work_intro), MAX_WORDS_BODY + 15), career_examples
    return work_intro or trim_words(tip_line, MAX_WORDS_BODY), career_examples


def _personalized_relationships(
    content: PersonalityResultContent,
    profile: Mapping[str, Any] | None,
    lang: str,
) -> str:
    base = _relationship_body(content)
    if profile is None:
        return base

    notes = profile.get("notes") or []
    ei_note = ""
    if notes and isinstance(notes[0], Mapping) and notes[0].get("ambiguous"):
        ei_note = str(notes[0].get("body") or "").strip()

    if not _firm_type_ok(profile):
        soft = t("result.premium.soft_type_note", lang)
        return _join_paragraphs(soft, ei_note, trim_words(base, 70) if base else "")

    if ei_note:
        return _join_paragraphs(ei_note, base)
    return base


def _personalized_actions(
    content: PersonalityResultContent,
    profile: Mapping[str, Any] | None,
    *,
    action_plan_override: str | None,
    lang: str,
) -> tuple[str, ...]:
    plan_bullets = _action_bullets(action_plan_override or content.action_plan or "")
    if profile is None:
        return plan_bullets

    scored: list[str] = []
    today = str(profile.get("today") or "").strip()
    if today:
        scored.append(trim_words(today, 32))
    for tip in profile.get("tips") or []:
        line = str(tip).strip()
        if line:
            scored.append(trim_words(line, 28))
        if len(scored) >= 3:
            break

    if not _firm_type_ok(profile):
        soft = trim_words(t("result.premium.soft_actions_note", lang), 28)
        return _merge_unique((soft, *scored), plan_bullets[:2], limit=ACTION_COUNT)

    return _merge_unique(tuple(scored), plan_bullets, limit=ACTION_COUNT)


def compose_premium_blocks(
    content: PersonalityResultContent,
    strengths: list[str],
    challenges: list[str],
    *,
    language: str,
    action_plan_override: str | None = None,
    profile: Mapping[str, Any] | None = None,
) -> tuple[PremiumBlock, ...]:
    lang = language
    work_intro, career_examples = _personalized_work(content, profile, lang)

    return (
        PremiumBlock(
            title_key="result.premium.brief",
            title=t("result.premium.brief", lang),
            body=_personalized_brief(content, profile, lang),
        ),
        PremiumBlock(
            title_key="result.premium.strengths",
            title=t("result.premium.strengths", lang),
            bullets=_personalized_strengths(content, strengths, profile, lang),
        ),
        PremiumBlock(
            title_key="result.premium.drains",
            title=t("result.premium.drains", lang),
            bullets=_personalized_drains(content, challenges, profile, lang),
        ),
        PremiumBlock(
            title_key="result.premium.work",
            title=t("result.premium.work", lang),
            body=work_intro,
            sub_bullets=career_examples,
        ),
        PremiumBlock(
            title_key="result.premium.relationships",
            title=t("result.premium.relationships", lang),
            body=_personalized_relationships(content, profile, lang),
        ),
        PremiumBlock(
            title_key="result.premium.actions",
            title=t("result.premium.actions", lang),
            bullets=_personalized_actions(
                content,
                profile,
                action_plan_override=action_plan_override,
                lang=lang,
            ),
        ),
    )
