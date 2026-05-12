from typing import Protocol, Any

from .schemas import ReviewEvaluationInput


class AuthenticityAnalyzer(Protocol):
    def analyze(self, review: ReviewEvaluationInput) -> dict[str, Any]:

        ...