from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Review:
    store: str
    product_url: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    rating: Optional[float] = None
    text: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    seller: Optional[str] = None
    is_verified_buyer: Optional[bool] = None
    helpful_yes: Optional[int] = None
    helpful_no: Optional[int] = None
    source_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
