from __future__ import annotations

import re
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

from .models import Review
from .utils import (
    DATE_RE,
    clean_text,
    dedupe_reviews,
    fetch_html,
    parse_int,
    select_text,
    soup_from_html,
)


class RozetkaParser:
    store_name = "rozetka"

    review_node_selector = "rz-comment"

    author_selector = '[data-testid="replay-header-author"]'
    date_selector = '[data-testid="replay-header-date"]'

    rating_attribute = "data-extracted-rating"

    variables_selector = ".comment__vars"
    text_selector = ".comment__body-wrapper > p"

    essentials_selector = ".comment__essentials > div"
    essential_label_selector = ".comment__essentials-label"
    essential_value_selector = "dd"

    helpful_yes_selector = (
        'button[aria-label="Корисний відгук"] '
        ".vote-buttons-comments__counter"
    )
    helpful_no_selector = (
        'button[aria-label="Некорисний відгук"] '
        ".vote-buttons-comments__counter"
    )

    def can_parse(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return host == "rozetka.com.ua" or host.endswith(".rozetka.com.ua")

    def parse(self, url: str, max_pages: int = 1) -> list[Review]:
        comments_url = self.to_comments_url(url)
        reviews: list[Review] = []

        for page_number in range(1, max_pages + 1):
            page_url = self.with_page(comments_url, page_number)
            html = self.load_page(page_url)
            soup = soup_from_html(html)

            nodes = soup.select(self.review_node_selector)

            if not nodes:
                if page_number == 1:
                    raise RuntimeError(
                        "Rozetka comments were not found. "
                        f"Selector: {self.review_node_selector}. "
                        "The page structure may have changed."
                    )

                break

            meta = self.extract_product_meta(soup=soup, product_url=comments_url)

            page_reviews = [
                review
                for node in nodes
                if (
                    review := self.parse_review_node(
                        node=node,
                        product_url=comments_url,
                        source_url=page_url,
                        product_id=meta.get("product_id"),
                        product_name=meta.get("product_name"),
                    )
                )
                is not None
            ]

            if not page_reviews:
                break

            reviews.extend(page_reviews)

        return dedupe_reviews(reviews)

    def load_page(self, page_url: str) -> str:
        html = fetch_html(page_url)

        if self.review_node_selector not in html:
            html = fetch_html(page_url, use_browser=True)

        return html

    def parse_review_node(
        self,
        node,
        product_url: str,
        source_url: str,
        product_id: Optional[str],
        product_name: Optional[str],
    ) -> Optional[Review]:
        author = select_text(node, self.author_selector)
        date = self.extract_date(node)
        rating = self.extract_rating(node)

        text = select_text(node, self.text_selector)
        pros, cons = self.extract_essentials(node)

        variables_text = select_text(node, self.variables_selector)
        seller = self.extract_seller(variables_text)
        is_verified_buyer = self.extract_verified_buyer(variables_text)

        helpful_yes = parse_int(select_text(node, self.helpful_yes_selector))
        helpful_no = parse_int(select_text(node, self.helpful_no_selector))

        if not text and not pros and not cons:
            return None

        return Review(
            store=self.store_name,
            product_url=product_url,
            product_id=product_id,
            product_name=product_name,
            author=author,
            date=date,
            rating=rating,
            text=text,
            pros=pros,
            cons=cons,
            seller=seller,
            is_verified_buyer=is_verified_buyer,
            helpful_yes=helpful_yes,
            helpful_no=helpful_no,
            source_url=source_url,
        )

    def extract_rating(self, node) -> Optional[float]:
        raw_rating = node.get(self.rating_attribute)

        if raw_rating is None:
            return None

        try:
            rating = float(str(raw_rating).replace(",", "."))
        except ValueError:
            return None

        if not 1 <= rating <= 5:
            return None

        return rating

    def extract_date(self, node) -> Optional[str]:
        raw_date = select_text(node, self.date_selector)

        if not raw_date:
            return None

        match = DATE_RE.search(raw_date)

        if match:
            return match.group(0)

        return raw_date

    def extract_essentials(self, node) -> tuple[Optional[str], Optional[str]]:
        pros = None
        cons = None

        for item in node.select(self.essentials_selector):
            label = select_text(item, self.essential_label_selector)
            value = select_text(item, self.essential_value_selector)

            if not label or not value:
                continue

            normalized_label = label.lower()

            if "переваги" in normalized_label or "достоинства" in normalized_label:
                pros = value
            elif "недоліки" in normalized_label or "недостатки" in normalized_label:
                cons = value

        return pros, cons

    def extract_seller(self, variables_text: Optional[str]) -> Optional[str]:
        if not variables_text:
            return None

        match = re.search(
            r"(?:Продавець|Продавец):\s*(.*?)(?=\s+(?:Колір|Цвет|Розмір|Размер|Пам'ять|Память):|$)",
            variables_text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return clean_text(match.group(1).strip(" ."))

    def extract_verified_buyer(self, variables_text: Optional[str]) -> Optional[bool]:
        if not variables_text:
            return None

        return (
            "Відгук від покупця" in variables_text
            or "Отзыв от покупателя" in variables_text
        )

    def extract_product_meta(
        self,
        soup: BeautifulSoup,
        product_url: str,
    ) -> dict[str, Optional[str]]:
        return {
            "product_url": product_url,
            "product_id": self.extract_product_id(soup),
            "product_name": self.extract_product_name(soup),
        }

    def extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")

        if not h1:
            return None

        product_name = clean_text(h1.get_text(" ", strip=True))

        if not product_name:
            return None

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

        return clean_text(product_name)

    def extract_product_id(self, soup: BeautifulSoup) -> Optional[str]:
        page_text = soup.get_text(" ", strip=True)
        match = re.search(r"(?:Код|Код товару):\s*([0-9]+)", page_text)

        if not match:
            return None

        return match.group(1)

    def to_comments_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path

        if "/comments" not in path:
            path = path.rstrip("/") + "/comments/"
        elif not path.endswith("/"):
            path += "/"

        return urlunparse(parsed._replace(path=path, query=""))

    def with_page(self, url: str, page_number: int) -> str:
        if page_number <= 1:
            return url

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query["page"] = [str(page_number)]

        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))