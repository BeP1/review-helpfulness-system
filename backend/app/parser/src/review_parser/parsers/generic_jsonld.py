from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from ..base import BaseParser
from ..models import Review
from ..utils import clean_text, dedupe_reviews, fetch_html, soup_from_html


class GenericJsonLdParser(BaseParser):
    store_name = "generic"

    def can_parse(self, url: str) -> bool:
        return bool(urlparse(url).netloc)

    def parse(self, url: str, max_pages: int = 1) -> List[Review]:
        html = fetch_html(url)
        soup = soup_from_html(html)
        scripts = soup.select("script[type='application/ld+json']")
        reviews: List[Review] = []

        product_name = None
        product_id = None
        for script in scripts:
            raw = script.string or script.get_text(strip=True)
            for item in self._safe_load_jsonld(raw):
                product_name = product_name or item.get("name")
                product_id = product_id or item.get("sku") or item.get("mpn")
                for review in self._extract_reviews(item):
                    reviews.append(
                        Review(
                            store=urlparse(url).netloc.replace("www.", ""),
                            product_url=url,
                            product_id=product_id,
                            product_name=product_name,
                            author=self._extract_author(review.get("author")),
                            date=review.get("datePublished"),
                            rating=self._extract_rating(review.get("reviewRating")),
                            text=clean_text(review.get("reviewBody") or review.get("description")),
                            source_url=url,
                        )
                    )

        return dedupe_reviews([r for r in reviews if r.text])

    def _safe_load_jsonld(self, raw: str) -> Iterable[Dict[str, Any]]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []

        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                return [x for x in data["@graph"] if isinstance(x, dict)]
            return [data]
        return []

    def _extract_reviews(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        reviews = item.get("review") or item.get("reviews") or []
        if isinstance(reviews, dict):
            return [reviews]
        if isinstance(reviews, list):
            return [x for x in reviews if isinstance(x, dict)]
        return []

    def _extract_author(self, author: Any) -> Optional[str]:
        if isinstance(author, dict):
            return clean_text(author.get("name"))
        if isinstance(author, str):
            return clean_text(author)
        return None

    def _extract_rating(self, rating: Any) -> Optional[float]:
        if isinstance(rating, dict):
            value = rating.get("ratingValue") or rating.get("value")
        else:
            value = rating
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None
