import hashlib
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Product, Review, ReviewAnalysis


def make_text_hash(text: str) -> str:
    normalized = " ".join(text.lower().strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_or_create_product(
    db: Session,
    url: str,
    source: str | None = None,
    title: str | None = None,
) -> Product:
    product = db.query(Product).filter(Product.url == url).first()

    if product:
        return product

    product = Product(
        url=url,
        source=source,
        title=title,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def save_reviews(
    db: Session,
    product: Product,
    reviews: list[dict[str, Any]],
) -> list[Review]:
    saved_reviews: list[Review] = []

    for review_data in reviews:
        external_id = (
            review_data.get("review_id")
            or review_data.get("external_id")
            or review_data.get("id")
        )

        text = (
            review_data.get("text")
            or review_data.get("review_text")
            or review_data.get("comment")
            or review_data.get("content")
            or ""
        ).strip()

        if not text:
            continue

        text_hash = make_text_hash(text)

        existing_review = None

        if external_id:
            existing_review = (
                db.query(Review)
                .filter(
                    Review.product_id == product.id,
                    Review.external_id == external_id,
                )
                .first()
            )

        if existing_review is None:
            existing_review = (
                db.query(Review)
                .filter(
                    Review.product_id == product.id,
                    Review.text_hash == text_hash,
                )
                .first()
            )

        if existing_review:
            saved_reviews.append(existing_review)
            continue

        review = Review(
            product_id=product.id,
            external_id=external_id,
            author=review_data.get("author"),
            rating=review_data.get("rating"),
            text=text,
            pros=review_data.get("pros"),
            cons=review_data.get("cons"),
            review_date=review_data.get("date") or review_data.get("review_date"),
            likes_count=review_data.get("likes_count"),
            text_hash=text_hash,
            raw_data=review_data,
        )

        db.add(review)
        saved_reviews.append(review)

    db.commit()

    for review in saved_reviews:
        db.refresh(review)

    return saved_reviews


def save_review_analysis(
    db: Session,
    review: Review,
    analysis_data: dict[str, Any],
    model_name: str | None = None,
) -> ReviewAnalysis:
    existing_analysis = (
        db.query(ReviewAnalysis)
        .filter(ReviewAnalysis.review_id == review.id)
        .first()
    )

    if existing_analysis:
        existing_analysis.helpfulness_score = analysis_data.get("helpfulness_score")
        existing_analysis.specificity_score = analysis_data.get("specificity_score")
        existing_analysis.usage_experience_score = analysis_data.get("usage_experience_score")
        existing_analysis.pros_cons_balance_score = analysis_data.get("pros_cons_balance_score")
        existing_analysis.decision_support_score = analysis_data.get("decision_support_score")
        existing_analysis.fake_probability = analysis_data.get("fake_probability")
        existing_analysis.category = analysis_data.get("category")
        existing_analysis.summary = analysis_data.get("summary")
        existing_analysis.model_name = model_name
        existing_analysis.raw_response = analysis_data.get("raw_response", analysis_data)

        db.commit()
        db.refresh(existing_analysis)

        return existing_analysis

    analysis = ReviewAnalysis(
        review_id=review.id,
        helpfulness_score=analysis_data.get("helpfulness_score"),
        specificity_score=analysis_data.get("specificity_score"),
        usage_experience_score=analysis_data.get("usage_experience_score"),
        pros_cons_balance_score=analysis_data.get("pros_cons_balance_score"),
        decision_support_score=analysis_data.get("decision_support_score"),
        fake_probability=analysis_data.get("fake_probability"),
        category=analysis_data.get("category"),
        summary=analysis_data.get("summary"),
        model_name=model_name,
        raw_response=analysis_data.get("raw_response", analysis_data),
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis