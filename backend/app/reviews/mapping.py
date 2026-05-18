from __future__ import annotations

from typing import Any

from ..evaluation import ReviewEvaluationInput


def get_first_value(
    data: dict[str, Any],
    keys: list[str],
    default: Any = None,
) -> Any:
    for key in keys:
        value = data.get(key)

        if value is not None:
            return value

    return default


def to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_evaluation_input(review: dict[str, Any]) -> ReviewEvaluationInput:
    llm_analysis = review.get("llm_analysis")
    analysis_data = review.get("analysis")

    if isinstance(llm_analysis, dict):
        analysis = {
            **review,
            "llm_analysis": llm_analysis,
            **llm_analysis,
        }
    elif isinstance(analysis_data, dict):
        analysis = {
            **review,
            "llm_analysis": analysis_data,
            **analysis_data,
        }
    else:
        analysis = review

    return ReviewEvaluationInput(
        review_id=get_first_value(review, ["review_id", "id"]),
        product_id=get_first_value(review, ["product_id"]),
        text=get_first_value(
            review,
            ["text", "comment", "review_text", "original_text", "body", "content"],
            "",
        ),
        prepared_text=get_first_value(
            review,
            [
                "review_text_for_llm",
                "prepared_text",
                "clean_text",
                "normalized_text",
                "text_for_llm",
                "llm_text",
            ],
        ),
        pros=get_first_value(review, ["pros", "advantages", "positive"]),
        cons=get_first_value(review, ["cons", "disadvantages", "negative"]),
        rating=to_float_or_none(get_first_value(review, ["rating", "score", "stars"])),
        author=get_first_value(review, ["author", "user", "username"]),
        created_at=get_first_value(review, ["created_at", "date", "published_at"]),
        source_url=get_first_value(
            review,
            ["source_url", "product_url", "url", "review_url"],
        ),
        analysis=analysis,
    )


def get_review_text_for_hash(review: dict[str, Any]) -> str:
    return get_first_value(
        review,
        ["text", "comment", "review_text", "original_text", "body", "content"],
        "",
    )


def build_analysis_data_for_db(payload: dict[str, Any]) -> dict[str, Any]:
    usefulness = payload.get("usefulness") or {}
    features = usefulness.get("features") or {}
    classification = payload.get("classification") or {}

    spam_risk = features.get("spam_risk")
    fake_probability = None

    if spam_risk is not None:
        try:
            fake_probability = float(spam_risk) / 10
        except (TypeError, ValueError):
            fake_probability = None

    return {
        "helpfulness_score": features.get("llm_helpfulness"),
        "specificity_score": features.get("specificity"),
        "usage_experience_score": features.get("usage_experience"),
        "pros_cons_balance_score": features.get("pros_cons_balance"),
        "decision_support_score": features.get("decision_support"),
        "fake_probability": fake_probability,
        "category": usefulness.get("category") or classification.get("topic_category"),
        "summary": payload.get("summary"),
        "raw_response": payload,
    }