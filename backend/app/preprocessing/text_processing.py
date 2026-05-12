from __future__ import annotations

import re
from typing import Any

from .constants import (
    SERVICE_PHRASES,
    UKRAINIAN_MARKERS,
    WORD_PATTERN,
    UKRAINIAN_SPECIFIC_LETTERS_PATTERN,
)


def normalize_text(value: Any | None) -> str | None:
    if value is None:
        return None

    text = str(value)

    for phrase in SERVICE_PHRASES:
        text = text.replace(phrase, " ")

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text or None


def count_words(text: str | None) -> int:
    if not text:
        return 0

    words = re.findall(WORD_PATTERN, text)
    return len(words)


def detect_language(text: str | None) -> str:
    if not text:
        return "unknown"

    lowered = text.lower()

    if re.search(UKRAINIAN_SPECIFIC_LETTERS_PATTERN, lowered):
        return "uk"

    uk_score = sum(
        1 for marker in UKRAINIAN_MARKERS
        if marker in lowered
    )

    if uk_score > 0:
        return "uk"

    return "unknown"