from __future__ import annotations

from typing import Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from .review_parser import parse_reviews_to_dicts
from .preprocessing.preparer import prepare_reviews_for_llm
from .llm.analyzer import ReviewHelpfulnessAnalyzer
from .evaluation import ReviewEvaluationInput, evaluate_reviews


app = FastAPI(
    title="Review Helpfulness System API",
    description="API for parsing, preparing, analyzing and evaluating product reviews."
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


class EvaluateReviewsRequest(BaseModel):
    reviews: List[dict[str, Any]]


class EvaluateReviewsResponse(BaseModel):
    input_count: int
    evaluated_count: int
    reviews: List[dict[str, Any]]


class ParsePrepareEvaluateResponse(BaseModel):
    store: str
    url: str
    raw_reviews_count: int
    prepared_reviews_count: int
    evaluated_reviews_count: int
    reviews: List[dict[str, Any]]


class ParsePrepareAnalyzeEvaluateResponse(BaseModel):
    store: str
    url: str
    raw_reviews_count: int
    prepared_reviews_count: int
    analyzed_reviews_count: int
    evaluated_reviews_count: int
    reviews: List[dict[str, Any]]


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
        review_id=get_first_value(
            review,
            ["review_id", "id"],
        ),
        product_id=get_first_value(
            review,
            ["product_id"],
        ),
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
        pros=get_first_value(
            review,
            ["pros", "advantages", "positive"],
        ),
        cons=get_first_value(
            review,
            ["cons", "disadvantages", "negative"],
        ),
        rating=to_float_or_none(
            get_first_value(
                review,
                ["rating", "score", "stars"],
            )
        ),
        author=get_first_value(
            review,
            ["author", "user", "username"],
        ),
        created_at=get_first_value(
            review,
            ["created_at", "date", "published_at"],
        ),
        source_url=get_first_value(
            review,
            ["source_url", "product_url", "url", "review_url"],
        ),
        analysis=analysis,
    )


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
    try:
        prepared_reviews = prepare_reviews_for_llm(
            reviews=request.reviews,
            include_low_information=request.include_low_information,
        )

        return PrepareReviewsResponse(
            input_count=len(request.reviews),
            prepared_count=len(prepared_reviews),
            reviews=prepared_reviews,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare reviews: {str(exc)}",
        ) from exc


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


@app.post("/api/reviews/evaluate", response_model=EvaluateReviewsResponse)
def evaluate_reviews_endpoint(
    request: EvaluateReviewsRequest,
) -> EvaluateReviewsResponse:
    try:
        evaluation_inputs = [
            build_evaluation_input(review)
            for review in request.reviews
        ]

        evaluated_reviews = evaluate_reviews(evaluation_inputs)

        return EvaluateReviewsResponse(
            input_count=len(request.reviews),
            evaluated_count=len(evaluated_reviews),
            reviews=[
                review.display_payload
                for review in evaluated_reviews
            ],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate reviews: {str(exc)}",
        ) from exc


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


@app.post(
    "/api/reviews/parse-prepare-evaluate",
    response_model=ParsePrepareEvaluateResponse,
)
def parse_prepare_evaluate_reviews(
    request: ParseReviewsRequest,
) -> ParsePrepareEvaluateResponse:
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

        evaluation_inputs = [
            build_evaluation_input(review)
            for review in prepared_reviews
        ]

        evaluated_reviews = evaluate_reviews(evaluation_inputs)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse, prepare and evaluate reviews: {str(exc)}",
        ) from exc

    store = raw_reviews[0].get("store", "unknown") if raw_reviews else "unknown"

    return ParsePrepareEvaluateResponse(
        store=store,
        url=url,
        raw_reviews_count=len(raw_reviews),
        prepared_reviews_count=len(prepared_reviews),
        evaluated_reviews_count=len(evaluated_reviews),
        reviews=[
            review.display_payload
            for review in evaluated_reviews
        ],
    )


@app.post(
    "/api/reviews/parse-prepare-analyze-evaluate",
    response_model=ParsePrepareAnalyzeEvaluateResponse,
)
def parse_prepare_analyze_evaluate_reviews(
    request: ParseReviewsRequest,
) -> ParsePrepareAnalyzeEvaluateResponse:
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

        evaluation_inputs = [
            build_evaluation_input(review)
            for review in analyzed_reviews
        ]

        evaluated_reviews = evaluate_reviews(evaluation_inputs)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse, prepare, analyze and evaluate reviews: {str(exc)}",
        ) from exc

    store = raw_reviews[0].get("store", "unknown") if raw_reviews else "unknown"

    return ParsePrepareAnalyzeEvaluateResponse(
        store=store,
        url=url,
        raw_reviews_count=len(raw_reviews),
        prepared_reviews_count=len(prepared_reviews),
        analyzed_reviews_count=len(analyzed_reviews),
        evaluated_reviews_count=len(evaluated_reviews),
        reviews=[
            review.display_payload
            for review in evaluated_reviews
        ],
    )