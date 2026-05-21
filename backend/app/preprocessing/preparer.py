from __future__ import annotations

from typing import Any

from .rating import normalize_rating
from .review_id import make_review_id
from .review_quality import is_low_information_review
from .review_text import build_llm_text
from .text_processing import (
    count_words,
    detect_language,
    normalize_text,
)


PRODUCT_CONTEXT_FIELDS = [
    "store",
    "product_url",
    "product_id",
    "product_name",
    "seller",
    "source_url",
]


def get_first_non_empty_value(
    reviews: list[dict[str, Any]],
    field: str,
) -> Any:
    for review in reviews:
        value = review.get(field)

        if value not in (None, "", []):
            return value

    return None


def extract_product_context(
    reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        field: get_first_non_empty_value(reviews, field)
        for field in PRODUCT_CONTEXT_FIELDS
    }


def prepare_review_for_llm(
    review: dict[str, Any],
    index: int = 0,
) -> dict[str, Any] | None:
    text = normalize_text(review.get("text"))
    pros = normalize_text(review.get("pros"))
    cons = normalize_text(review.get("cons"))

    llm_text = build_llm_text(text, pros, cons)

    if not llm_text:
        return None

    rating = normalize_rating(review.get("rating"))
    word_count = count_words(llm_text)

    return {
        "review_id": make_review_id(review, index),
        "author": normalize_text(review.get("author")),
        "date": normalize_text(review.get("date")),
        "rating": rating,
        "is_verified_buyer": bool(review.get("is_verified_buyer")),
        "helpful_yes": review.get("helpful_yes"),
        "helpful_no": review.get("helpful_no"),
        "language": detect_language(llm_text),
        "text": text,
        "pros": pros,
        "cons": cons,
        "review_text_for_llm": llm_text,
        "char_count": len(llm_text),
        "word_count": word_count,
        "has_text": bool(text),
        "has_pros": bool(pros),
        "has_cons": bool(cons),
        "has_rating": rating is not None,
        "is_low_information": is_low_information_review(
            text=text,
            pros=pros,
            cons=cons,
            word_count=word_count,
        ),
    }


def prepare_reviews_for_llm(
    reviews: list[dict[str, Any]],
    include_low_information: bool = True,
) -> dict[str, Any]:
    """
    Builds compact LLM payload.

    Product-level fields are moved to the top-level 'product' object.
    Each review contains only review-specific fields.
    """
    product_context = extract_product_context(reviews)

    prepared_reviews = []

    for index, review in enumerate(reviews):
        prepared = prepare_review_for_llm(review, index=index)

        if prepared is None:
            continue

        if not include_low_information and prepared["is_low_information"]:
            continue

        prepared_reviews.append(prepared)

    return {
        "product": product_context,
        "reviews_count": len(prepared_reviews),
        "reviews": prepared_reviews,
    }