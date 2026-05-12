from __future__ import annotations

import re


def build_llm_text(
    text: str | None,
    pros: str | None,
    cons: str | None,
) -> str | None:
    parts = []

    if text:
        parts.append(f"Коментар: {text}")

    if pros:
        parts.append(f"Переваги: {pros}")

    if cons:
        parts.append(f"Недоліки: {cons}")

    result = ". ".join(parts)
    result = re.sub(r"\s+", " ", result).strip()

    return result or None