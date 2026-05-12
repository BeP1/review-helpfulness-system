from __future__ import annotations

from typing import Any


def normalize_rating(value: Any | None) -> int | None:
    if value is None:
        return None

    try:
        rating = int(float(value))
    except (TypeError, ValueError):
        return None

    if 1 <= rating <= 5:
        return rating

    return None