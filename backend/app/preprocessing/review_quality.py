from __future__ import annotations

from .constants import LOW_INFORMATION_PHRASES


def is_low_information_review(
    text: str | None,
    pros: str | None,
    cons: str | None,
    word_count: int,
) -> bool:
    combined = " ".join(
        part for part in [text, pros, cons]
        if part
    ).lower().strip()

    if word_count <= 2:
        return True

    if combined in LOW_INFORMATION_PHRASES:
        return True

    if word_count < 5 and not pros and not cons:
        return True

    return False