from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)
    pros: Mapped[str | None] = mapped_column(Text, nullable=True)
    cons: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    likes_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    product: Mapped["Product"] = relationship(back_populates="reviews")
    analysis: Mapped["ReviewAnalysis"] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "external_id",
            name="uq_review_product_external_id",
        ),
        UniqueConstraint(
            "product_id",
            "text_hash",
            name="uq_review_product_text_hash",
        ),
    )


class ReviewAnalysis(Base):
    __tablename__ = "review_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    helpfulness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    specificity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_experience_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pros_cons_balance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decision_support_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fake_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    review: Mapped["Review"] = relationship(back_populates="analysis")