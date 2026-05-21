from typing import Any

from .llm_client import ReviewLLMClient
from .rules import rule_based_low_information_analysis


class ReviewHelpfulnessAnalyzer:
    def __init__(self, llm_client: ReviewLLMClient | None = None) -> None:
        self.llm_client = llm_client or ReviewLLMClient()

    def _build_payload(
        self,
        review: dict[str, Any],
        product_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "product": {
                "store": product_context.get("store"),
                "product_id": product_context.get("product_id"),
                "product_name": product_context.get("product_name"),
                "seller": product_context.get("seller"),
            },
            "review": {
                "review_id": review.get("review_id"),
                "rating": review.get("rating"),
                "is_verified_buyer": review.get("is_verified_buyer"),
                "helpful_yes": review.get("helpful_yes"),
                "helpful_no": review.get("helpful_no"),
                "language": review.get("language"),
                "word_count": review.get("word_count"),
                "has_pros": review.get("has_pros"),
                "has_cons": review.get("has_cons"),
                "text": review.get("review_text_for_llm"),
            },
        }

    def _build_analyzed_review(
        self,
        review: dict[str, Any],
        product_context: dict[str, Any],
        analysis: dict[str, Any],
        analysis_source: str,
    ) -> dict[str, Any]:
        """
        Keeps compact review fields, but adds product fields needed by
        evaluation/mapping code after LLM analysis.
        """
        return {
            **review,
            "product": product_context,
            "product_id": product_context.get("product_id"),
            "product_name": product_context.get("product_name"),
            "source_url": product_context.get("source_url"),
            "llm_analysis": analysis,
            "analysis_source": analysis_source,
        }

    def analyze_review(
        self,
        review: dict[str, Any],
        product_context: dict[str, Any],
        skip_low_information: bool = True,
    ) -> dict[str, Any]:
        if skip_low_information and review.get("is_low_information"):
            analysis = rule_based_low_information_analysis(review)

            return self._build_analyzed_review(
                review=review,
                product_context=product_context,
                analysis=analysis,
                analysis_source="rule_based",
            )

        payload = self._build_payload(
            review=review,
            product_context=product_context,
        )

        analysis = self.llm_client.analyze(payload)

        return self._build_analyzed_review(
            review=review,
            product_context=product_context,
            analysis=analysis,
            analysis_source="llm",
        )

    def analyze_reviews(
        self,
        reviews: list[dict[str, Any]],
        product_context: dict[str, Any],
        limit: int | None = None,
        skip_low_information: bool = True,
    ) -> list[dict[str, Any]]:
        selected_reviews = reviews[:limit] if limit else reviews

        return [
            self.analyze_review(
                review=review,
                product_context=product_context,
                skip_low_information=skip_low_information,
            )
            for review in selected_reviews
        ]