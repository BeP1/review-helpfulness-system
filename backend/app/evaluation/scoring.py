from .schemas import (
    LLMHelpfulnessAnalysis,
    UsefulnessCategory,
    UsefulnessFeatures,
)


def build_features_from_llm(
    llm_analysis: LLMHelpfulnessAnalysis,
) -> UsefulnessFeatures:
    return UsefulnessFeatures(
        llm_helpfulness=llm_analysis.helpfulness_score,
        specificity=llm_analysis.specificity_score,
        usage_experience=llm_analysis.usage_experience_score,
        pros_cons_balance=llm_analysis.pros_cons_balance_score,
        decision_support=llm_analysis.decision_support_score,
        spam_risk=llm_analysis.spam_risk_score,
    )


def calculate_usefulness_score_from_llm(
    llm_analysis: LLMHelpfulnessAnalysis,
) -> int:
    """
    Converts LLM analysis from 0-10 scale to stable final 0-100 score.

    The final score is based mainly on the LLM helpfulness score,
    but it is cross-checked with detailed sub-scores.

    spam_risk_score is not fake detection here.
    It only slightly penalizes generic/promotional/spam-like reviews.
    """

    base_score_0_10 = (
        llm_analysis.helpfulness_score * 0.40
        + llm_analysis.specificity_score * 0.20
        + llm_analysis.usage_experience_score * 0.15
        + llm_analysis.pros_cons_balance_score * 0.10
        + llm_analysis.decision_support_score * 0.15
    )

    base_score_0_100 = base_score_0_10 * 10

    spam_penalty = llm_analysis.spam_risk_score * 1.5

    final_score = base_score_0_100 - spam_penalty

    return round(_clamp(final_score, 0, 100))


def determine_usefulness_category(
    score: int,
) -> UsefulnessCategory:
    if score >= 80:
        return UsefulnessCategory.VERY_USEFUL

    if score >= 60:
        return UsefulnessCategory.USEFUL

    if score >= 40:
        return UsefulnessCategory.PARTIALLY_USEFUL

    if score >= 20:
        return UsefulnessCategory.LOW_USEFULNESS

    return UsefulnessCategory.NOT_USEFUL


def determine_is_helpful(
    score: int,
    llm_analysis: LLMHelpfulnessAnalysis,
) -> bool:
    """
    Final helpfulness decision.

    A review is considered helpful only if:
    - final score is high enough;
    - LLM also marked it as helpful;
    - spam risk is not too high.
    """

    if score < 60:
        return False

    if not llm_analysis.is_helpful:
        return False

    if llm_analysis.spam_risk_score >= 7:
        return False

    return True


def _clamp(
    value: float,
    min_value: float,
    max_value: float,
) -> float:
    return max(min_value, min(value, max_value))