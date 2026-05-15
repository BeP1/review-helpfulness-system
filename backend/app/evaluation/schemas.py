from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UsefulnessCategory(str, Enum):
    VERY_USEFUL = "very_useful"
    USEFUL = "useful"
    PARTIALLY_USEFUL = "partially_useful"
    LOW_USEFULNESS = "low_usefulness"
    NOT_USEFUL = "not_useful"


class ReviewTopicCategory(str, Enum):
    PRODUCT_QUALITY = "product_quality"
    DELIVERY_SERVICE = "delivery_service"
    PRICE_VALUE = "price_value"
    USABILITY = "usability"
    DURABILITY = "durability"
    COMPATIBILITY = "compatibility"
    CUSTOMER_SERVICE = "customer_service"
    GENERAL_IMPRESSION = "general_impression"
    LOW_INFORMATION = "low_information"
    OTHER = "other"


class ReviewSentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class LLMHelpfulnessAnalysis(BaseModel):
    helpfulness_score: int = Field(ge=0, le=10)
    specificity_score: int = Field(ge=0, le=10)
    usage_experience_score: int = Field(ge=0, le=10)
    pros_cons_balance_score: int = Field(ge=0, le=10)
    decision_support_score: int = Field(ge=0, le=10)
    spam_risk_score: int = Field(ge=0, le=10)

    category: ReviewTopicCategory
    sentiment: ReviewSentiment
    is_helpful: bool

    summary: str
    explanation: str


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

    analysis: dict[str, Any] = Field(default_factory=dict)


class UsefulnessFeatures(BaseModel):
    llm_helpfulness: float
    specificity: float
    usage_experience: float
    pros_cons_balance: float
    decision_support: float
    spam_risk: float


class ReviewEvaluationResult(BaseModel):
    review_id: str | None
    product_id: str | None

    text: str
    rating: float | None
    author: str | None
    created_at: str | None
    source_url: str | None

    usefulness_score: int
    usefulness_category: UsefulnessCategory
    is_helpful: bool

    topic_category: ReviewTopicCategory
    sentiment: ReviewSentiment

    features: UsefulnessFeatures

    summary: str
    explanation: str

    storage_payload: dict[str, Any]
    display_payload: dict[str, Any]