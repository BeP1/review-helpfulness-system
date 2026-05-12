from typing import Any

from .schemas import UsefulnessCategory, UsefulnessFeatures


PRODUCT_ASPECT_WORDS = [
    "якість",
    "ціна",
    "розмір",
    "матеріал",
    "екран",
    "батарея",
    "акумулятор",
    "камера",
    "звук",
    "доставка",
    "упаковка",
    "зручність",
    "швидкість",
    "памʼять",
    "пам'ять",
    "корпус",
    "заряд",
    "гарантія",
    "комплектація",
    "функція",
    "працює",
    "підключення",
    "налаштування",
    "вага",
    "потужність",
    "шум",
    "температура",
]


EXPERIENCE_WORDS = [
    "користуюсь",
    "користувався",
    "користувалась",
    "використовую",
    "використовував",
    "використовувала",
    "купив",
    "купила",
    "замовив",
    "замовила",
    "тестував",
    "тестувала",
    "перевірив",
    "перевірила",
    "після",
    "тиждень",
    "тижня",
    "місяць",
    "місяця",
    "день",
    "днів",
    "разів",
    "працює",
    "працював",
    "працювала",
]


BALANCE_WORDS = [
    "але",
    "проте",
    "однак",
    "хоча",
    "мінус",
    "плюс",
    "перевага",
    "переваги",
    "недолік",
    "недоліки",
    "з одного боку",
    "з іншого боку",
]


DECISION_WORDS = [
    "рекомендую",
    "не рекомендую",
    "раджу",
    "не раджу",
    "варто",
    "не варто",
    "підійде",
    "не підійде",
    "можна брати",
    "краще не брати",
]


def build_usefulness_features(
    text: str,
    pros: str | None,
    cons: str | None,
    rating: float | None,
    analysis: dict[str, Any],
) -> UsefulnessFeatures:
    normalized = _normalize(text)

    return UsefulnessFeatures(
        specificity=_score_from_analysis(
            analysis=analysis,
            keys=["specificity_score", "specificity"],
            fallback=_heuristic_specificity(normalized),
        ),
        usage_experience=_score_from_analysis(
            analysis=analysis,
            keys=["usage_experience_score", "experience_score", "usage_experience"],
            fallback=_heuristic_usage_experience(normalized),
        ),
        pros_cons_balance=_score_from_analysis(
            analysis=analysis,
            keys=["pros_cons_balance_score", "balance_score", "pros_cons_balance"],
            fallback=_heuristic_balance(normalized, pros, cons),
        ),
        decision_support=_score_from_analysis(
            analysis=analysis,
            keys=["decision_support_score", "decision_support"],
            fallback=_heuristic_decision_support(normalized, rating),
        ),
        text_quality=_score_from_analysis(
            analysis=analysis,
            keys=["text_quality_score", "text_quality"],
            fallback=_heuristic_text_quality(normalized),
        ),
        rating_context=_score_from_analysis(
            analysis=analysis,
            keys=["rating_context_score", "rating_context"],
            fallback=_heuristic_rating_context(normalized, rating),
        ),
    )


def calculate_usefulness_score(features: UsefulnessFeatures) -> int:
    score = (
        features.specificity * 0.25
        + features.usage_experience * 0.20
        + features.pros_cons_balance * 0.15
        + features.decision_support * 0.25
        + features.text_quality * 0.10
        + features.rating_context * 0.05
    )

    return round(_clamp(score * 10, 0, 100))


def determine_usefulness_category(score: int) -> UsefulnessCategory:
    if score >= 80:
        return UsefulnessCategory.VERY_USEFUL

    if score >= 60:
        return UsefulnessCategory.USEFUL

    if score >= 40:
        return UsefulnessCategory.PARTIALLY_USEFUL

    if score >= 20:
        return UsefulnessCategory.LOW_USEFULNESS

    return UsefulnessCategory.NOT_USEFUL


def is_helpful_review(score: int) -> bool:
    return score >= 60


def _heuristic_specificity(text: str) -> float:
    if not text:
        return 0

    words = text.split()
    aspect_hits = sum(1 for word in PRODUCT_ASPECT_WORDS if word in text)
    has_number = any(char.isdigit() for char in text)

    score = 0

    if len(words) >= 8:
        score += 2

    if len(words) >= 20:
        score += 2

    if aspect_hits >= 1:
        score += 2

    if aspect_hits >= 3:
        score += 2

    if has_number:
        score += 1

    if len(text) >= 180:
        score += 1

    return _clamp(score, 0, 10)


def _heuristic_usage_experience(text: str) -> float:
    if not text:
        return 0

    hits = sum(1 for word in EXPERIENCE_WORDS if word in text)

    score = hits * 2.2

    if "після" in text and any(
        word in text
        for word in ["день", "днів", "тиждень", "тижня", "місяць", "місяця"]
    ):
        score += 2

    return _clamp(score, 0, 10)


def _heuristic_balance(
    text: str,
    pros: str | None,
    cons: str | None,
) -> float:
    score = 0

    if pros:
        score += 3

    if cons:
        score += 3

    balance_hits = sum(1 for word in BALANCE_WORDS if word in text)

    score += min(balance_hits * 2, 4)

    return _clamp(score, 0, 10)


def _heuristic_decision_support(
    text: str,
    rating: float | None,
) -> float:
    if not text:
        return 0

    words = text.split()
    score = 0

    if len(words) >= 10:
        score += 2

    if len(words) >= 25:
        score += 2

    if any(word in text for word in PRODUCT_ASPECT_WORDS):
        score += 2

    if any(word in text for word in EXPERIENCE_WORDS):
        score += 2

    if rating is not None:
        score += 1

    if any(word in text for word in DECISION_WORDS):
        score += 1

    return _clamp(score, 0, 10)


def _heuristic_text_quality(text: str) -> float:
    if not text:
        return 0

    words = text.split()

    if len(words) <= 3:
        return 2

    unique_ratio = len(set(words)) / len(words)

    score = 6

    if len(words) >= 12:
        score += 2

    if unique_ratio >= 0.65:
        score += 2

    if unique_ratio < 0.45:
        score -= 3

    return _clamp(score, 0, 10)


def _heuristic_rating_context(
    text: str,
    rating: float | None,
) -> float:
    if rating is None:
        return 4

    if not text:
        return 1

    words = text.split()

    if len(words) >= 10:
        return 8

    if len(words) >= 5:
        return 5

    return 2


def _score_from_analysis(
    analysis: dict[str, Any],
    keys: list[str],
    fallback: float,
) -> float:
    for key in keys:
        value = analysis.get(key)

        if value is None:
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        return _clamp(numeric_value, 0, 10)

    return _clamp(fallback, 0, 10)


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))