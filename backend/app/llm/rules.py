from typing import Any


def rule_based_low_information_analysis(review: dict[str, Any]) -> dict[str, Any]:
    text = review.get("review_text_for_llm") or ""

    return {
        "helpfulness_score": 1,
        "specificity_score": 1,
        "usage_experience_score": 0,
        "pros_cons_balance_score": 0,
        "decision_support_score": 1,
        "spam_risk_score": 2,
        "category": "low_information",
        "sentiment": "neutral",
        "is_helpful": False,
        "summary": text[:120] if text else "Low-information review.",
        "explanation": "The review is too short or generic to provide meaningful help for a potential buyer.",
    }