from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.repository import (
    get_or_create_product,
    make_text_hash,
    save_review_analysis,
    save_reviews,
)
from ..evaluation import evaluate_reviews
from ..llm.analyzer import ReviewHelpfulnessAnalyzer
from ..preprocessing.preparer import prepare_reviews_for_llm
from ..review_parser import parse_reviews_to_dicts
from .mapping import (
    build_analysis_data_for_db,
    build_evaluation_input,
    get_review_text_for_hash,
)
from .schemas import ParsePrepareAnalyzeEvaluateResponse


def parse_prepare_analyze_evaluate_and_save(
    *,
    db: Session,
    url: str,
    max_pages: int,
) -> ParsePrepareAnalyzeEvaluateResponse:
    raw_reviews = parse_reviews_to_dicts(
        url=url,
        max_pages=max_pages,
    )

    store = raw_reviews[0].get("store", "unknown") if raw_reviews else "unknown"

    product = get_or_create_product(
        db=db,
        url=url,
        source=store,
        title=None,
    )

    saved_reviews = save_reviews(
        db=db,
        product=product,
        reviews=raw_reviews,
    )

    saved_reviews_by_external_id = {
        str(review.external_id): review
        for review in saved_reviews
        if review.external_id
    }

    saved_reviews_by_hash = {
        review.text_hash: review
        for review in saved_reviews
        if review.text_hash
    }

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

    evaluated_payloads = [
        review.display_payload
        for review in evaluated_reviews
    ]

    saved_analyses_count = 0

    for index, payload in enumerate(evaluated_payloads):
        saved_review = find_saved_review_for_payload(
            payload=payload,
            index=index,
            saved_reviews=saved_reviews,
            saved_reviews_by_external_id=saved_reviews_by_external_id,
            saved_reviews_by_hash=saved_reviews_by_hash,
        )

        if saved_review is None:
            continue

        external_id = (
            payload.get("review_id")
            or payload.get("external_id")
            or payload.get("id")
        )

        if external_id and not saved_review.external_id:
            saved_review.external_id = str(external_id)
            db.add(saved_review)
            db.commit()
            db.refresh(saved_review)

        analysis_data = build_analysis_data_for_db(payload)

        save_review_analysis(
            db=db,
            review=saved_review,
            analysis_data=analysis_data,
            model_name="llm",
        )

        saved_analyses_count += 1

    return ParsePrepareAnalyzeEvaluateResponse(
        store=store,
        url=url,
        product_id=product.id,
        raw_reviews_count=len(raw_reviews),
        prepared_reviews_count=len(prepared_reviews),
        analyzed_reviews_count=len(analyzed_reviews),
        evaluated_reviews_count=len(evaluated_reviews),
        saved_reviews_count=len(saved_reviews),
        saved_analyses_count=saved_analyses_count,
        reviews=evaluated_payloads,
    )


def find_saved_review_for_payload(
    *,
    payload: dict,
    index: int,
    saved_reviews: list,
    saved_reviews_by_external_id: dict,
    saved_reviews_by_hash: dict,
):
    external_id = (
        payload.get("review_id")
        or payload.get("external_id")
        or payload.get("id")
    )

    if external_id:
        saved_review = saved_reviews_by_external_id.get(str(external_id))

        if saved_review is not None:
            return saved_review

    review_text = get_review_text_for_hash(payload)

    if review_text:
        review_hash = make_text_hash(review_text)
        saved_review = saved_reviews_by_hash.get(review_hash)

        if saved_review is not None:
            return saved_review

    if index < len(saved_reviews):
        return saved_reviews[index]

    return None