from __future__ import annotations

from typing import Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from .review_parser import parse_reviews_from_url, parse_reviews_to_dicts
from .preprocessing.preparer import prepare_reviews_for_llm
from .llm.analyzer import ReviewHelpfulnessAnalyzer


app = FastAPI(
    title="Review Helpfulness System API",
    description="API for parsing product reviews from online stores.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseReviewsRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=1, ge=1, le=10)


class ParseReviewsResponse(BaseModel):
    store: str
    url: str
    reviews_count: int
    reviews: List[dict[str, Any]]


class PrepareReviewsRequest(BaseModel):
    reviews: List[dict[str, Any]]
    include_low_information: bool = True


class PrepareReviewsResponse(BaseModel):
    input_count: int
    prepared_count: int
    reviews: List[dict[str, Any]]


class AnalyzeReviewsRequest(BaseModel):
    reviews: List[dict[str, Any]]
    limit: int | None = Field(default=None, ge=1, le=100)
    skip_low_information: bool = True


class AnalyzeReviewsResponse(BaseModel):
    input_count: int
    analyzed_count: int
    reviews: List[dict[str, Any]]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Review Helpfulness System API is running"
    }


@app.post("/api/reviews/parse", response_model=ParseReviewsResponse)
def parse_reviews(request: ParseReviewsRequest) -> ParseReviewsResponse:
    url = str(request.url)

    try:
        reviews = parse_reviews_to_dicts(
            url=url,
            max_pages=request.max_pages,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse reviews: {str(exc)}",
        ) from exc

    store = reviews[0].get("store", "unknown") if reviews else "unknown"

    return ParseReviewsResponse(
        store=store,
        url=url,
        reviews_count=len(reviews),
        reviews=reviews,
    )


@app.post("/api/reviews/prepare", response_model=PrepareReviewsResponse)
def prepare_reviews(request: PrepareReviewsRequest) -> PrepareReviewsResponse:
    prepared_reviews = prepare_reviews_for_llm(
        reviews=request.reviews,
        include_low_information=request.include_low_information,
    )

    return PrepareReviewsResponse(
        input_count=len(request.reviews),
        prepared_count=len(prepared_reviews),
        reviews=prepared_reviews,
    )


@app.post("/api/reviews/parse-and-prepare")
def parse_and_prepare_reviews(request: ParseReviewsRequest) -> dict[str, Any]:
    url = str(request.url)

    try:
        raw_reviews = parse_reviews_to_dicts(
            url=url,
            max_pages=request.max_pages,
        )

        prepared_reviews = prepare_reviews_for_llm(
            reviews=raw_reviews,
            include_low_information=True,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse and prepare reviews: {str(exc)}",
        ) from exc

    store = raw_reviews[0].get("store", "unknown") if raw_reviews else "unknown"

    return {
        "store": store,
        "url": url,
        "raw_reviews_count": len(raw_reviews),
        "prepared_reviews_count": len(prepared_reviews),
        "reviews": prepared_reviews,
    }


@app.post("/api/reviews/analyze", response_model=AnalyzeReviewsResponse)
def analyze_reviews(request: AnalyzeReviewsRequest) -> AnalyzeReviewsResponse:
    try:
        analyzer = ReviewHelpfulnessAnalyzer()

        analyzed_reviews = analyzer.analyze_reviews(
            reviews=request.reviews,
            limit=request.limit,
            skip_low_information=request.skip_low_information,
        )

        return AnalyzeReviewsResponse(
            input_count=len(request.reviews),
            analyzed_count=len(analyzed_reviews),
            reviews=analyzed_reviews,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze reviews with LLM: {str(exc)}",
        ) from exc


@app.post("/api/reviews/parse-prepare-analyze")
def parse_prepare_analyze_reviews(request: ParseReviewsRequest) -> dict[str, Any]:
    url = str(request.url)

    try:
        raw_reviews = parse_reviews_to_dicts(
            url=url,
            max_pages=request.max_pages,
        )

        prepared_reviews = prepare_reviews_for_llm(
            reviews=raw_reviews,
            include_low_information=True,
        )

        analyzer = ReviewHelpfulnessAnalyzer()

        analyzed_reviews = analyzer.analyze_reviews(
            reviews=prepared_reviews,
            skip_low_information=True,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse, prepare and analyze reviews: {str(exc)}",
        ) from exc

    store = raw_reviews[0].get("store", "unknown") if raw_reviews else "unknown"

    return {
        "store": store,
        "url": url,
        "raw_reviews_count": len(raw_reviews),
        "prepared_reviews_count": len(prepared_reviews),
        "analyzed_reviews_count": len(analyzed_reviews),
        "reviews": analyzed_reviews,
    }