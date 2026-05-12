from __future__ import annotations

import hashlib
import re
from typing import Any, Optional


SERVICE_PHRASES = [
    "Відгук від покупця",
    "Отзыв от покупателя",
    "Відповісти",
    "Ответить",
]


UKRAINIAN_MARKERS = [
    "переваги",
    "недоліки",
    "користуюсь",
    "користувався",
    "товар",
    "якість",
    "швидко",
    "добре",
    "погано",
    "продавець",
]


RUSSIAN_MARKERS = [
    "достоинства",
    "недостатки",
    "пользуюсь",
    "пользовался",
    "товар",
    "качество",
    "быстро",
    "хорошо",
    "плохо",
    "продавец",
]


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    text = str(value)

    for phrase in SERVICE_PHRASES:
        text = text.replace(phrase, " ")

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text or None


def normalize_rating(value: Any) -> Optional[int]:
    if value is None:
        return None

    try:
        rating = int(float(value))

        if 1 <= rating <= 5:
            return rating

    except (TypeError, ValueError):
        return None

    return None


def count_words(text: Optional[str]) -> int:
    if not text:
        return 0

    words = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґЁё0-9]+", text)
    return len(words)


def detect_language(text: Optional[str]) -> str:
    if not text:
        return "unknown"

    lowered = text.lower()

    uk_score = sum(1 for marker in UKRAINIAN_MARKERS if marker in lowered)
    ru_score = sum(1 for marker in RUSSIAN_MARKERS if marker in lowered)

    if uk_score > ru_score:
        return "uk"

    if ru_score > uk_score:
        return "ru"

    if re.search(r"[іїєґ]", lowered):
        return "uk"

    if re.search(r"[ыэъё]", lowered):
        return "ru"

    return "unknown"


def build_llm_text(
    text: Optional[str],
    pros: Optional[str],
    cons: Optional[str],
) -> Optional[str]:
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


def is_low_information_review(
    text: Optional[str],
    pros: Optional[str],
    cons: Optional[str],
    word_count: int,
) -> bool:
    combined = " ".join(
        part for part in [text, pros, cons] if part
    ).lower()

    very_short_phrases = {
        "ок",
        "ok",
        "норм",
        "нормально",
        "супер",
        "добре",
        "хорошо",
        "клас",
        "класс",
        "рекомендую",
        "дякую",
        "спасибо",
    }

    if word_count <= 2:
        return True

    if combined.strip() in very_short_phrases:
        return True

    if word_count < 5 and not pros and not cons:
        return True

    return False


def prepare_review_for_llm(
    review: dict[str, Any],
    index: int = 0,
) -> Optional[dict[str, Any]]:
    text = normalize_text(review.get("text"))
    pros = normalize_text(review.get("pros"))
    cons = normalize_text(review.get("cons"))

    llm_text = build_llm_text(text, pros, cons)

    if not llm_text:
        return None

    rating = normalize_rating(review.get("rating"))
    word_count = count_words(llm_text)
    language = detect_language(llm_text)

    prepared = {
        "review_id": make_review_id(review, index),
        "store": review.get("store"),
        "product_url": review.get("product_url"),
        "product_id": review.get("product_id"),
        "product_name": review.get("product_name"),
        "author": normalize_text(review.get("author")),
        "date": normalize_text(review.get("date")),
        "rating": rating,
        "is_verified_buyer": bool(review.get("is_verified_buyer")),
        "helpful_yes": review.get("helpful_yes"),
        "helpful_no": review.get("helpful_no"),
        "language": language,
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
        "source_url": review.get("source_url"),
    }

    return prepared


def prepare_reviews_for_llm(
    reviews: list[dict[str, Any]],
    include_low_information: bool = True,
) -> list[dict[str, Any]]:
    prepared_reviews = []

    for index, review in enumerate(reviews):
        prepared = prepare_review_for_llm(review, index=index)

        if prepared is None:
            continue

        if not include_low_information and prepared["is_low_information"]:
            continue

        prepared_reviews.append(prepared)

    return prepared_reviews