from __future__ import annotations

from .models import Review
from .rozetka import RozetkaParser


def parse_reviews_from_url(url: str, max_pages: int = 1) -> list[Review]:
    parsers = [
        RozetkaParser(),
    ]

    for parser in parsers:
        if parser.can_parse(url):
            return parser.parse(url=url, max_pages=max_pages)

    raise ValueError(f"Unsupported review source: {url}")


def parse_reviews_to_dicts(url: str, max_pages: int = 1) -> list[dict]:
    reviews = parse_reviews_from_url(url=url, max_pages=max_pages)
    return [review.to_dict() for review in reviews]