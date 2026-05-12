from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

from ..base import BaseParser
from ..models import Review
from ..utils import (
    DATE_RE,
    clean_lines,
    clean_text,
    dedupe_reviews,
    fetch_html,
    first_text,
    soup_from_html,
)


class RozetkaParser(BaseParser):
    store_name = "rozetka"

    REVIEW_NODE_SELECTORS = [
        "rz-comment",
        "div.comment",
        "li.comment",
        "div.comments__item",
        "li.comments__item",
        "app-comment",
        "[class*='comment'][class*='item']",
    ]

    AUTHOR_SELECTORS = [
        "rz-reply-header [class*='author']",
        "rz-reply-header [class*='user']",
        ".comment__author",
        ".comment__user-name",
        ".comments__author",
        "[class*='author']",
        "[class*='user-name']",
    ]

    DATE_SELECTORS = [
        ".comment__date",
        ".comments__date",
        "time",
        "[class*='date']",
    ]

    TEXT_SELECTORS = [
        ".comment__body-wrapper",
        ".comment__text",
        ".comments__text",
        "[class*='body-wrapper']",
        "[class*='comment'][class*='text']",
    ]

    def can_parse(self, url: str) -> bool:
        return "rozetka.com.ua" in urlparse(url).netloc.lower()

    def parse(self, url: str, max_pages: int = 1) -> List[Review]:
        reviews: List[Review] = []
        comments_url = self._to_comments_url(url)

        for page in range(1, max_pages + 1):
            page_url = self._with_page(comments_url, page)

            html = fetch_html(page_url)
            soup = soup_from_html(html)
            meta = self._extract_product_meta(soup, comments_url)

            page_reviews = self._parse_with_selectors(
                soup=soup,
                meta=meta,
                product_url=comments_url,
                source_url=page_url,
            )



            if not page_reviews:
                page_reviews = self._parse_with_text_fallback(
                    soup=soup,
                    meta=meta,
                    product_url=comments_url,
                    source_url=page_url,
                )

                print(
                    f"[INFO] Page {page}: fallback parsed {len(page_reviews)} reviews. "
                    f"Ratings are not available in text fallback."
                )

            if not page_reviews:
                break

            reviews.extend(page_reviews)

        return dedupe_reviews(reviews)

    def _to_comments_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path

        if "/comments" not in path:
            path = path.rstrip("/") + "/comments/"
        elif not path.endswith("/"):
            path += "/"

        return urlunparse(parsed._replace(path=path, query=""))

    def _with_page(self, url: str, page: int) -> str:
        if page <= 1:
            return url

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query["page"] = [str(page)]

        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _extract_product_meta(
        self,
        soup: BeautifulSoup,
        product_url: str,
    ) -> Dict[str, Optional[str]]:
        h1 = soup.find("h1")
        product_name = clean_text(h1.get_text(" ", strip=True)) if h1 else None

        if product_name:
            product_name = re.sub(
                r"^Відгуки покупців про\s+",
                "",
                product_name,
                flags=re.IGNORECASE,
            )
            product_name = re.sub(
                r"^Отзывы покупателей о\s+",
                "",
                product_name,
                flags=re.IGNORECASE,
            )

        full_text = soup.get_text("\n", strip=True)

        product_id_match = re.search(r"Код:\s*([0-9]+)", full_text)
        product_id = product_id_match.group(1) if product_id_match else None

        overall_rating_match = re.search(
            r"Оцінка користувачів\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*5",
            full_text,
            flags=re.IGNORECASE,
        )
        overall_rating = (
            overall_rating_match.group(1).replace(",", ".")
            if overall_rating_match
            else None
        )

        review_count_match = re.search(r"Відгуки\s*\((\d+)\)", full_text)
        review_count = review_count_match.group(1) if review_count_match else None

        return {
            "product_url": product_url,
            "product_id": product_id,
            "product_name": product_name,
            "overall_rating": overall_rating,
            "review_count": review_count,
        }

    def _extract_rating_from_node(self, node) -> Optional[int]:
        injected_rating = node.get("data-extracted-rating")

        if injected_rating:
            try:
                rating = int(float(injected_rating))

                if 1 <= rating <= 5:
                    return rating
            except ValueError:
                pass

        rating_element = node.select_one(
            '[data-testid="stars-rating"], .stars__rating, [class*="stars__rating"], [class*="stars-rating"]'
        )

        if not rating_element:
            return None

        style = rating_element.get("style", "")

        match = re.search(
            r"calc\(\s*20%\s*\*\s*([1-5](?:[.,]\d+)?)\s*(?:px)?\s*\)",
            style,
            flags=re.IGNORECASE,
        )

        if match:
            rating = round(float(match.group(1).replace(",", ".")))
            return rating if 1 <= rating <= 5 else None

        match = re.search(
            r"width\s*:\s*(\d+(?:[.,]\d+)?)\s*%",
            style,
            flags=re.IGNORECASE,
        )

        if match:
            width_percent = float(match.group(1).replace(",", "."))
            rating = round(width_percent / 20)
            return rating if 1 <= rating <= 5 else None

        return None

    def _extract_pros_cons_from_text(
        self,
        text: Optional[str],
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        if not text:
            return None, None, None

        body = text
        pros = None
        cons = None

        pros_match = re.search(
            r"Переваги:\s*(.*?)(?:Недоліки:|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        cons_match = re.search(
            r"Недоліки:\s*(.*)$",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if pros_match:
            pros = clean_text(pros_match.group(1))
            body = re.sub(
                r"Переваги:\s*.*",
                "",
                body,
                flags=re.IGNORECASE | re.DOTALL,
            )

        if cons_match:
            cons = clean_text(cons_match.group(1))
            body = re.sub(
                r"Недоліки:\s*.*",
                "",
                body,
                flags=re.IGNORECASE | re.DOTALL,
            )

        return clean_text(body), pros, cons

    def _parse_with_selectors(
        self,
        soup: BeautifulSoup,
        meta: Dict[str, Optional[str]],
        product_url: str,
        source_url: str,
    ) -> List[Review]:
        nodes: List = []

        for selector in self.REVIEW_NODE_SELECTORS:
            found_nodes = soup.select(selector)

            if found_nodes:
                nodes = found_nodes
                break

        reviews: List[Review] = []

        for node in nodes:
            raw_text = clean_text(node.get_text(" ", strip=True))

            if not raw_text:
                continue

            if self._looks_like_seller_reply(raw_text):
                continue

            # Skip tiny technical/non-review blocks
            rating = self._extract_rating_from_node(node)
            has_date = DATE_RE.search(raw_text) is not None

            if rating is None and not has_date:
                continue

            author = first_text(node, self.AUTHOR_SELECTORS)

            date = first_text(node, self.DATE_SELECTORS)

            if date:
                match = DATE_RE.search(date)
                date = match.group(0) if match else date
            else:
                match = DATE_RE.search(raw_text)
                date = match.group(0) if match else None

            text = first_text(node, self.TEXT_SELECTORS) or raw_text

            # Remove technical UI words from text
            text = re.sub(r"\bВідповісти\b.*$", "", text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r"\bОтветить\b.*$", "", text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r"Відгук від покупця\.?", "", text, flags=re.IGNORECASE)
            text = re.sub(r"Отзыв от покупателя\.?", "", text, flags=re.IGNORECASE)

            text, pros, cons = self._extract_pros_cons_from_text(text)

            seller_match = re.search(r"Продавець:\s*([^\.]+?)(?:\s|$)", raw_text)
            seller = clean_text(seller_match.group(1)) if seller_match else None

            helpful_yes, helpful_no = self._extract_helpful_votes(raw_text)

            review = Review(
                store=self.store_name,
                product_url=product_url,
                product_id=meta.get("product_id"),
                product_name=meta.get("product_name"),
                author=author,
                date=date,
                rating=rating,
                text=text,
                pros=pros,
                cons=cons,
                seller=seller,
                is_verified_buyer=(
                    "Відгук від покупця" in raw_text
                    or "Отзыв от покупателя" in raw_text
                ),
                helpful_yes=helpful_yes,
                helpful_no=helpful_no,
                source_url=source_url,
            )

            if review.text:
                reviews.append(review)

        return reviews

    def _parse_with_text_fallback(
        self,
        soup: BeautifulSoup,
        meta: Dict[str, Optional[str]],
        product_url: str,
        source_url: str,
    ) -> List[Review]:
        lines = clean_lines(soup.get_text("\n", strip=True))

        start = 0

        for i, line in enumerate(lines):
            if "Фільтри" in line or "Фильтры" in line:
                start = i + 1
                break

        lines = lines[start:]

        reviews: List[Review] = []
        i = 0

        while i < len(lines) - 1:
            author = lines[i]
            date_line = lines[i + 1]

            if not DATE_RE.search(date_line):
                i += 1
                continue

            if self._looks_like_seller_name(author):
                i += 2
                continue

            date = DATE_RE.search(date_line).group(0)
            i += 2

            block: List[str] = []

            while i < len(lines):
                if (
                    i + 1 < len(lines)
                    and DATE_RE.search(lines[i + 1])
                    and not self._looks_like_seller_name(lines[i])
                ):
                    break

                block.append(lines[i])

                if lines[i] in {"Відповісти", "Ответить"}:
                    if i + 1 < len(lines) and re.fullmatch(r"\d+\s+\d+", lines[i + 1]):
                        block.append(lines[i + 1])
                        i += 1

                    i += 1
                    break

                i += 1

            raw_text = "\n".join(block)

            if self._looks_like_seller_reply(raw_text):
                continue

            seller = None
            seller_match = re.search(r"Продавець:\s*([^\n]+)", raw_text)

            if seller_match:
                seller = clean_text(seller_match.group(1))

            is_verified = (
                "Відгук від покупця" in raw_text
                or "Отзыв от покупателя" in raw_text
            )

            raw_text = re.sub(
                r"Відгук від покупця\.??",
                "",
                raw_text,
                flags=re.IGNORECASE,
            )
            raw_text = re.sub(
                r"Отзыв от покупателя\.??",
                "",
                raw_text,
                flags=re.IGNORECASE,
            )
            raw_text = re.sub(r"Продавець:\s*[^\n]+", "", raw_text)
            raw_text = re.sub(
                r"(?:Відповісти|Ответить).*",
                "",
                raw_text,
                flags=re.DOTALL,
            )

            text, pros, cons = self._extract_pros_cons_from_text(raw_text)
            helpful_yes, helpful_no = self._extract_helpful_votes("\n".join(block))

            if text:
                reviews.append(
                    Review(
                        store=self.store_name,
                        product_url=product_url,
                        product_id=meta.get("product_id"),
                        product_name=meta.get("product_name"),
                        author=clean_text(author),
                        date=date,
                        rating=None,
                        text=text,
                        pros=pros,
                        cons=cons,
                        seller=seller,
                        is_verified_buyer=is_verified,
                        helpful_yes=helpful_yes,
                        helpful_no=helpful_no,
                        source_url=source_url,
                    )
                )

        return reviews

    def _extract_helpful_votes(self, text: str) -> tuple[Optional[int], Optional[int]]:
        lines = clean_lines(text)

        for idx, line in enumerate(lines):
            if line in {"Відповісти", "Ответить"} and idx + 1 < len(lines):
                match = re.fullmatch(r"(\d+)\s+(\d+)", lines[idx + 1])

                if match:
                    return int(match.group(1)), int(match.group(2))

        match = re.search(r"(?:Відповісти|Ответить)\s+(\d+)\s+(\d+)", text)

        if match:
            return int(match.group(1)), int(match.group(2))

        return None, None

    def _looks_like_seller_name(self, value: str) -> bool:
        value_lower = value.lower()

        return any(
            token in value_lower
            for token in [
                "представник",
                "представитель",
                "постачальник",
                "бренд",
            ]
        )

    def _looks_like_seller_reply(self, text: str) -> bool:
        low = text.lower()

        return low.startswith("представник") or low.startswith("представитель")