"""Plain-language reading of stored dimension scores.

The four-letter type still selects the long description. This module only
says which side of each pair received more points, and when the two sides
were too close for a firm conclusion. It does not invent answers or percentages.
"""

from __future__ import annotations

from app.i18n import t as translate
from app.personality.constants import DIMENSION_LOW_CONFIDENCE_MAX_GAP

_PAIRS: tuple[tuple[str, str, str, str], ...] = (
    ("result.formed.ei.title", "ei", "e", "i"),
    ("result.formed.sn.title", "sn", "s", "n"),
    ("result.formed.tf.title", "tf", "t", "f"),
    ("result.formed.jp.title", "jp", "j", "p"),
)


def explain_dimensions(
    *,
    e: int,
    i: int,
    s: int,
    n: int,
    t: int,
    f: int,
    j: int,
    p: int,
    language: str,
) -> list[dict[str, str | bool]]:
    scores = {"e": e, "i": i, "s": s, "n": n, "t": t, "f": f, "j": j, "p": p}
    notes: list[dict[str, str | bool]] = []
    for title_key, pair, left, right in _PAIRS:
        left_score = int(scores[left])
        right_score = int(scores[right])
        gap = abs(left_score - right_score)
        ambiguous = gap <= DIMENSION_LOW_CONFIDENCE_MAX_GAP
        if left_score == right_score:
            body_key = f"result.formed.{pair}.tie"
        elif ambiguous:
            winner = left if left_score > right_score else right
            body_key = f"result.formed.{pair}.close_{winner}"
        else:
            winner = left if left_score > right_score else right
            body_key = f"result.formed.{pair}.{winner}"
        notes.append(
            {
                "title": translate(title_key, language),
                "body": translate(body_key, language),
                "ambiguous": ambiguous,
            }
        )
    return notes
