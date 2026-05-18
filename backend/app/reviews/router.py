from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_db
from .pipeline import parse_prepare_analyze_evaluate_and_save
from .schemas import (
    ParsePrepareAnalyzeEvaluateResponse,
    ParseReviewsRequest,
)


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