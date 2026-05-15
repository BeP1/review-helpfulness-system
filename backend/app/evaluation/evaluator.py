from typing import Any

from pydantic import ValidationError

from .schemas import (
    LLMHelpfulnessAnalysis,
    ReviewEvaluationInput,
    ReviewEvaluationResult,
)
from .scoring import (
    build_features_from_llm,
    calculate_usefulness_score_from_llm,
    determine_is_helpful,
    determine_usefulness_category,
)


def evaluate_review(
    review: ReviewEvaluationInput,
) -> ReviewEvaluationResult:
    text = _build_text_for_evaluation(review)

    llm_analysis = _extract_llm_analysis(review.analysis)

    features = build_features_from_llm(llm_analysis)

    usefulness_score = calculate_usefulness_score_from_llm(llm_analysis)

    usefulness_category = determine_usefulness_category(usefulness_score)

    is_helpful = determine_is_helpful(
        score=usefulness_score,
        llm_analysis=llm_analysis,
    )

    storage_payload = _build_storage_payload(
        review=review,
        text=text,
        llm_analysis=llm_analysis,
        usefulness_score=usefulness_score,
        usefulness_category=usefulness_category.value,
        is_helpful=is_helpful,
        features=features.model_dump(),
    )

    display_payload = _build_display_payload(
        review=review,
        text=text,
        llm_analysis=llm_analysis,
        usefulness_score=usefulness_score,
        usefulness_category=usefulness_category.value,
        is_helpful=is_helpful,
        features=features.model_dump(),
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
        usefulness_category=usefulness_category,
        is_helpful=is_helpful,
        topic_category=llm_analysis.category,
        sentiment=llm_analysis.sentiment,
        features=features,
        summary=llm_analysis.summary,
        explanation=llm_analysis.explanation,
        storage_payload=storage_payload,
        display_payload=display_payload,
    )


def evaluate_reviews(
    reviews: list[ReviewEvaluationInput],
) -> list[ReviewEvaluationResult]:
    return [
        evaluate_review(review)
        for review in reviews
    ]


def _extract_llm_analysis(
    analysis: dict[str, Any],
) -> LLMHelpfulnessAnalysis:
    """
    Supports two formats:

    1. Nested format:
       {
           "llm_analysis": {...}
       }

    2. Flattened format:
       {
           "helpfulness_score": 5,
           "specificity_score": 2,
           ...
       }
    """

    raw_llm_analysis = analysis.get("llm_analysis")

    if isinstance(raw_llm_analysis, dict):
        data = raw_llm_analysis
    else:
        data = analysis

    try:
        return LLMHelpfulnessAnalysis.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            "Evaluation requires a valid llm_analysis object that matches "
            "HELPFULNESS_SCHEMA."
        ) from exc


def _build_text_for_evaluation(
    review: ReviewEvaluationInput,
) -> str:
    parts = []

    if review.prepared_text:
        parts.append(review.prepared_text)
    elif review.text:
        parts.append(review.text)

    return " ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def _build_storage_payload(
    review: ReviewEvaluationInput,
    text: str,
    llm_analysis: LLMHelpfulnessAnalysis,
    usefulness_score: int,
    usefulness_category: str,
    is_helpful: bool,
    features: dict[str, float],
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
        "usefulness_category": usefulness_category,
        "is_helpful": is_helpful,

        "topic_category": llm_analysis.category.value,
        "sentiment": llm_analysis.sentiment.value,

        "features": features,

        "llm_analysis": llm_analysis.model_dump(),

        "summary": llm_analysis.summary,
        "explanation": llm_analysis.explanation,
    }


def _build_display_payload(
    review: ReviewEvaluationInput,
    text: str,
    llm_analysis: LLMHelpfulnessAnalysis,
    usefulness_score: int,
    usefulness_category: str,
    is_helpful: bool,
    features: dict[str, float],
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
            "category": usefulness_category,
            "is_helpful": is_helpful,
            "features": features,
        },

        "classification": {
            "topic_category": llm_analysis.category.value,
            "sentiment": llm_analysis.sentiment.value,
        },

        "summary": llm_analysis.summary,
        "explanation": llm_analysis.explanation,
    }