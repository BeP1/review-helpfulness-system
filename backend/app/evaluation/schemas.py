from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UsefulnessCategory(str, Enum):
    VERY_USEFUL = "very_useful"
    USEFUL = "useful"
    PARTIALLY_USEFUL = "partially_useful"
    LOW_USEFULNESS = "low_usefulness"
    NOT_USEFUL = "not_useful"


class ReviewEvaluationInput(BaseModel):
    review_id: str | None = None
    product_id: str | None = None

    text: str = ""
    prepared_text: str | None = None

    pros: str | None = None
    cons: str | None = None

    rating: float | None = None
    author: str | None = None
    created_at: str | None = None
    source_url: str | None = None

    # сюди можна передати результат LLM-аналізу, якщо він уже є
    analysis: dict[str, Any] = Field(default_factory=dict)


class UsefulnessFeatures(BaseModel):
    specificity: float
    usage_experience: float
    pros_cons_balance: float
    decision_support: float
    text_quality: float
    rating_context: float


class ReviewEvaluationResult(BaseModel):
    review_id: str | None
    product_id: str | None

    text: str
    rating: float | None
    author: str | None
    created_at: str | None
    source_url: str | None

    usefulness_score: int
    category: UsefulnessCategory
    is_helpful: bool

    features: UsefulnessFeatures

    summary: str | None = None
    explanation: str | None = None

    # зараз не використовується, але залишено як точка розширення
    authenticity: dict[str, Any] | None = None

    storage_payload: dict[str, Any]
    display_payload: dict[str, Any]