from __future__ import annotations

import hashlib
from typing import Any


def make_review_id(review: dict[str, Any], index: int) -> str:
    raw = "|".join(
        str(review.get(key) or "")
        for key in [
            "store",
            "product_id",
            "author",
            "date",
            "text",
            "pros",
            "cons",
        ]
    )

    if not raw.strip("|"):
        raw = str(index)

    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    store = review.get("store") or "store"
    product_id = review.get("product_id") or "product"

    return f"{store}_{product_id}_{digest}"