from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session


from ..db.session import get_db

from .pipeline import parse_prepare_analyze_evaluate_and_save
from .schemas import (
    ParsePrepareAnalyzeEvaluateResponse,
    ParseReviewsRequest,
)
from typing import Any

from pydantic import BaseModel

from ..db.repository import (
    get_or_create_product,
    save_reviews,
)
from ..llm.analyzer import ReviewHelpfulnessAnalyzer
from ..preprocessing import prepare_reviews_for_llm
from ..review_parser import parse_reviews_to_dicts

router = APIRouter(
    prefix="/api/reviews",
    tags=["reviews"],
)


@router.post(
    "/parse-prepare-analyze-evaluate",
    response_model=ParsePrepareAnalyzeEvaluateResponse,
)
def parse_prepare_analyze_evaluate_reviews(
    request: ParseReviewsRequest,
    db: Session = Depends(get_db),
) -> ParsePrepareAnalyzeEvaluateResponse:
    try:
        return parse_prepare_analyze_evaluate_and_save(
            db=db,
            url=str(request.url),
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
            detail=f"Failed to parse, prepare, analyze, evaluate and save reviews: {str(exc)}",
        ) from exc

@router.post("/debug/parse")
def debug_parse_reviews(request: ParseReviewsRequest):
    try:
        raw_reviews = parse_reviews_to_dicts(
            url=str(request.url),
            max_pages=request.max_pages,
        )

        return {
            "url": str(request.url),
            "reviews_count": len(raw_reviews),
            "reviews": raw_reviews,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse reviews: {str(exc)}",
        ) from exc


class PrepareReviewsRequest(BaseModel):
    reviews: list[dict[str, Any]]
    include_low_information: bool = True


@router.post("/debug/prepare")
def debug_prepare_reviews(request: PrepareReviewsRequest):
    try:
        prepared_payload = prepare_reviews_for_llm(
            reviews=request.reviews,
            include_low_information=request.include_low_information,
        )

        return {
            "input_reviews_count": len(request.reviews),
            "product": prepared_payload["product"],
            "prepared_reviews_count": prepared_payload["reviews_count"],
            "prepared_reviews": prepared_payload["reviews"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare reviews: {str(exc)}",
        ) from exc


@router.post("/debug/parse-prepare")
def debug_parse_prepare_reviews(request: ParseReviewsRequest):
    try:
        raw_reviews = parse_reviews_to_dicts(
            url=str(request.url),
            max_pages=request.max_pages,
        )

        prepared_payload = prepare_reviews_for_llm(
            reviews=raw_reviews,
            include_low_information=True,
        )

        return {
            "url": str(request.url),
            "raw_reviews_count": len(raw_reviews),
            "product": prepared_payload["product"],
            "prepared_reviews_count": prepared_payload["reviews_count"],
            "prepared_reviews": prepared_payload["reviews"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse and prepare reviews: {str(exc)}",
        ) from exc


class AnalyzeReviewsRequest(BaseModel):
    product: dict[str, Any]
    reviews: list[dict[str, Any]]
    skip_low_information: bool = True


@router.post("/debug/analyze")
def debug_analyze_reviews(request: AnalyzeReviewsRequest):
    try:
        analyzer = ReviewHelpfulnessAnalyzer()

        analyzed_reviews = analyzer.analyze_reviews(
            reviews=request.reviews,
            product_context=request.product,
            skip_low_information=request.skip_low_information,
        )

        return {
            "product": request.product,
            "input_reviews_count": len(request.reviews),
            "analyzed_reviews_count": len(analyzed_reviews),
            "analyzed_reviews": analyzed_reviews,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze reviews: {str(exc)}",
        ) from exc


@router.post("/debug/parse-prepare-analyze")
def debug_parse_prepare_analyze_reviews(request: ParseReviewsRequest):
    try:
        raw_reviews = parse_reviews_to_dicts(
            url=str(request.url),
            max_pages=request.max_pages,
        )

        prepared_payload = prepare_reviews_for_llm(
            reviews=raw_reviews,
            include_low_information=True,
        )

        product_context = prepared_payload["product"]
        prepared_reviews = prepared_payload["reviews"]

        analyzer = ReviewHelpfulnessAnalyzer()

        analyzed_reviews = analyzer.analyze_reviews(
            reviews=prepared_reviews,
            product_context=product_context,
            skip_low_information=True,
        )

        return {
            "url": str(request.url),
            "product": product_context,
            "raw_reviews_count": len(raw_reviews),
            "prepared_reviews_count": len(prepared_reviews),
            "analyzed_reviews_count": len(analyzed_reviews),
            "analyzed_reviews": analyzed_reviews,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse, prepare and analyze reviews: {str(exc)}",
        ) from exc


@router.post("/debug/parse-save")
def debug_parse_and_save_reviews(
    request: ParseReviewsRequest,
    db: Session = Depends(get_db),
):
    try:
        raw_reviews = parse_reviews_to_dicts(
            url=str(request.url),
            max_pages=request.max_pages,
        )

        store = raw_reviews[0].get("store", "unknown") if raw_reviews else "unknown"

        product = get_or_create_product(
            db=db,
            url=str(request.url),
            source=store,
            title=None,
        )

        saved_reviews = save_reviews(
            db=db,
            product=product,
            reviews=raw_reviews,
        )

        return {
            "url": str(request.url),
            "store": store,
            "product_id": product.id,
            "parsed_reviews_count": len(raw_reviews),
            "saved_reviews_count": len(saved_reviews),
            "saved_review_ids": [review.id for review in saved_reviews],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse and save reviews: {str(exc)}",
        ) from exc