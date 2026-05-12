from typing import Any

from .rules import rule_based_low_information_analysis
from .llm_client import ReviewLLMClient

class ReviewHelpfulnessAnalyzer:
    def __init__(self, llm_client: ReviewLLMClient | None = None) -> None:
        self.llm_client = llm_client or ReviewLLMClient()

    def _build_payload(self, review: dict[str, Any]) -> dict[str, Any]:
        return {
            "review_id": review.get("review_id"),
            "product_name": review.get("product_name"),
            "rating": review.get("rating"),
            "is_verified_buyer": review.get("is_verified_buyer"),
            "helpful_yes": review.get("helpful_yes"),
            "helpful_no": review.get("helpful_no"),
            "language": review.get("language"),
            "word_count": review.get("word_count"),
            "has_pros": review.get("has_pros"),
            "has_cons": review.get("has_cons"),
            "review_text": review.get("review_text_for_llm"),
        }

    def analyze_review(
        self,
        review: dict[str, Any],
        skip_low_information: bool = True,
    ) -> dict[str, Any]:

        if skip_low_information and review.get("is_low_information"):
            analysis = rule_based_low_information_analysis(review)

            return {
                **review,
                "llm_analysis": analysis,
                "analysis_source": "rule_based",
            }

        payload = self._build_payload(review)
        analysis = self.llm_client.analyze(payload)

        return {
            **review,
            "llm_analysis": analysis,
            "analysis_source": "llm",
        }

    def analyze_reviews(
        self,
        reviews: list[dict[str, Any]],
        limit: int | None = None,
        skip_low_information: bool = True,
    ) -> list[dict[str, Any]]:

        selected_reviews = reviews[:limit] if limit else reviews

        return [
            self.analyze_review(
                review=review,
                skip_low_information=skip_low_information,
            )
            for review in selected_reviews
        ]