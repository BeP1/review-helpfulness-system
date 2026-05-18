from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ParseReviewsRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=1, ge=1, le=10)


class ParsePrepareAnalyzeEvaluateResponse(BaseModel):
    store: str
    url: str
    product_id: int | None = None

    raw_reviews_count: int
    prepared_reviews_count: int
    analyzed_reviews_count: int
    evaluated_reviews_count: int

    saved_reviews_count: int
    saved_analyses_count: int

    reviews: list[dict[str, Any]]