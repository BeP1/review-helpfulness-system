from typing import Any

from .interfaces import AuthenticityAnalyzer
from .schemas import ReviewEvaluationInput, ReviewEvaluationResult
from .scoring import (
    build_usefulness_features,
    calculate_usefulness_score,
    determine_usefulness_category,
    is_helpful_review,
)


def evaluate_review(
    review: ReviewEvaluationInput,
    authenticity_analyzer: AuthenticityAnalyzer | None = None,
) -> ReviewEvaluationResult:
    text = _build_text_for_evaluation(review)

    features = build_usefulness_features(
        text=text,
        pros=review.pros,
        cons=review.cons,
        rating=review.rating,
        analysis=review.analysis,
    )

    usefulness_score = calculate_usefulness_score(features)
    category = determine_usefulness_category(usefulness_score)
    is_helpful = is_helpful_review(usefulness_score)

    summary = _extract_optional_string(
        review.analysis,
        keys=["summary", "short_summary"],
    )

    explanation = _extract_optional_string(
        review.analysis,
        keys=["explanation", "reason", "comment"],
    )

    authenticity = None

    # Зараз це не використовується.
    # Пізніше сюди можна підключити fake/authenticity module без зміни evaluator.
    if authenticity_analyzer is not None:
        authenticity = authenticity_analyzer.analyze(review)

    storage_payload = _build_storage_payload(
        review=review,
        text=text,
        usefulness_score=usefulness_score,
        category=category.value,
        is_helpful=is_helpful,
        features=features.model_dump(),
        summary=summary,
        explanation=explanation,
        authenticity=authenticity,
    )

    display_payload = _build_display_payload(
        review=review,
        text=text,
        usefulness_score=usefulness_score,
        category=category.value,
        is_helpful=is_helpful,
        features=features.model_dump(),
        summary=summary,
        explanation=explanation,
    )

    return ReviewEvaluationResult(
        review_id=review.review_id,
        product_id=review.product_id,
        text=text,
        rating=review.rating,
        author=review.author,
        created_at=review.created_at,
        source_url=review.source_url,
        usefulness_score=usefulness_score,
        category=category,
        is_helpful=is_helpful,
        features=features,
        summary=summary,
        explanation=explanation,
        authenticity=authenticity,
        storage_payload=storage_payload,
        display_payload=display_payload,
    )


def evaluate_reviews(
    reviews: list[ReviewEvaluationInput],
    authenticity_analyzer: AuthenticityAnalyzer | None = None,
) -> list[ReviewEvaluationResult]:
    return [
        evaluate_review(
            review=review,
            authenticity_analyzer=authenticity_analyzer,
        )
        for review in reviews
    ]


def _build_text_for_evaluation(review: ReviewEvaluationInput) -> str:
    parts = []

    if review.prepared_text:
        parts.append(review.prepared_text)
    elif review.text:
        parts.append(review.text)

    if review.pros:
        parts.append(f"Переваги: {review.pros}")

    if review.cons:
        parts.append(f"Недоліки: {review.cons}")

    return " ".join(part.strip() for part in parts if part and part.strip())


def _build_storage_payload(
    review: ReviewEvaluationInput,
    text: str,
    usefulness_score: int,
    category: str,
    is_helpful: bool,
    features: dict[str, float],
    summary: str | None,
    explanation: str | None,
    authenticity: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "review_id": review.review_id,
        "product_id": review.product_id,
        "text": text,
        "rating": review.rating,
        "author": review.author,
        "created_at": review.created_at,
        "source_url": review.source_url,
        "usefulness_score": usefulness_score,
        "category": category,
        "is_helpful": is_helpful,
        "features": features,
        "summary": summary,
        "explanation": explanation,

        # Зараз буде None.
        # Пізніше сюди можна зберігати результат fake/authenticity analysis.
        "authenticity": authenticity,
    }


def _build_display_payload(
    review: ReviewEvaluationInput,
    text: str,
    usefulness_score: int,
    category: str,
    is_helpful: bool,
    features: dict[str, float],
    summary: str | None,
    explanation: str | None,
) -> dict[str, Any]:
    return {
        "review_id": review.review_id,
        "text": text,
        "rating": review.rating,
        "author": review.author,
        "created_at": review.created_at,
        "source_url": review.source_url,
        "usefulness": {
            "score": usefulness_score,
            "category": category,
            "is_helpful": is_helpful,
            "features": features,
        },
        "summary": summary,
        "explanation": explanation,
    }


def _extract_optional_string(
    data: dict[str, Any],
    keys: list[str],
) -> str | None:
    for key in keys:
        value = data.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None