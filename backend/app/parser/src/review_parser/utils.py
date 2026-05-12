from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .models import Review


UA_RU_MONTHS = (
    "січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня|"
    "января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
)

DATE_RE = re.compile(
    rf"\b\d{{1,2}}\s+(?:{UA_RU_MONTHS})\s+\d{{4}}\b",
    re.IGNORECASE,
)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6",
    "Connection": "keep-alive",
    "Referer": "https://rozetka.com.ua/ua/",
}


def fetch_html(url: str, delay_sec: float = 1.0, timeout: int = 30) -> str:
    """
    Loads public HTML.

    First tries requests.
    If the site blocks normal HTTP requests with 403/429,
    falls back to Playwright Chromium.
    """

    time.sleep(delay_sec)

    try:
        session = requests.Session()
        response = session.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.text

    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None

        if status_code in {403, 429}:
            print(f"[INFO] Requests blocked with status {status_code}. Trying Playwright...")
            return fetch_html_with_browser(url, timeout=timeout)

        raise


def fetch_html_with_browser(url: str, timeout: int = 30) -> str:
    """
    Opens the page with Playwright Chromium and returns rendered HTML.

    For Rozetka, it tries to extract review ratings directly inside the browser
    and injects them into each rz-comment as data-extracted-rating.
    """

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run:\n"
            "pip install playwright\n"
            "python -m playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="uk-UA",
            timezone_id="Europe/Kyiv",
            viewport={
                "width": 1366,
                "height": 900,
            },
            extra_http_headers={
                "Accept": DEFAULT_HEADERS["Accept"],
                "Accept-Language": DEFAULT_HEADERS["Accept-Language"],
                "Referer": DEFAULT_HEADERS["Referer"],
            },
        )

        page = context.new_page()

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout * 1000,
            )

            page.wait_for_selector("rz-comment", timeout=timeout * 1000)
            page.wait_for_timeout(3000)

            # Scroll slowly so lazy-loaded elements inside reviews are rendered
            for _ in range(12):
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(600)

            page.wait_for_timeout(2000)

            injected_count = page.evaluate(
                """
                () => {
                    function parseRatingFromStyle(style) {
                        if (!style) return null;

                        // Example:
                        // width: calc(20% * 2px);
                        // width: calc(20% * 2);
                        let calcMatch = style.match(/calc\\(\\s*20%\\s*\\*\\s*([1-5](?:[\\.,]\\d+)?)\\s*(?:px)?\\s*\\)/i);

                        if (calcMatch) {
                            let rating = Math.round(parseFloat(calcMatch[1].replace(",", ".")));

                            if (rating >= 1 && rating <= 5) {
                                return rating;
                            }
                        }

                        // Example:
                        // width: 80%;
                        let percentMatch = style.match(/width\\s*:\\s*(\\d+(?:[\\.,]\\d+)?)\\s*%/i);

                        if (percentMatch) {
                            let width = parseFloat(percentMatch[1].replace(",", "."));
                            let rating = Math.round(width / 20);

                            if (rating >= 1 && rating <= 5) {
                                return rating;
                            }
                        }

                        return null;
                    }

                    function parseRatingFromComment(comment) {
                        // 1. First try known rating elements
                        const directSelectors = [
                            '[data-testid="stars-rating"]',
                            '.stars__rating',
                            '[class*="stars__rating"]',
                            '[class*="stars-rating"]',
                            '[class*="rating"]'
                        ];

                        for (const selector of directSelectors) {
                            const elements = Array.from(comment.querySelectorAll(selector));

                            for (const element of elements) {
                                const style = element.getAttribute("style") || "";
                                const rating = parseRatingFromStyle(style);

                                if (rating !== null) {
                                    return rating;
                                }
                            }
                        }

                        // 2. Then scan ALL styled elements inside the comment
                        const styledElements = Array.from(comment.querySelectorAll("[style]"));

                        for (const element of styledElements) {
                            const style = element.getAttribute("style") || "";
                            const rating = parseRatingFromStyle(style);

                            if (rating !== null) {
                                return rating;
                            }
                        }

                        // 3. Last fallback: computed width ratio
                        const possibleRatingElements = Array.from(
                            comment.querySelectorAll('[data-testid="stars-rating"], .stars__rating, [class*="stars__rating"]')
                        );

                        for (const element of possibleRatingElements) {
                            const parent = element.parentElement;

                            if (!parent) continue;

                            const elementWidth = element.getBoundingClientRect().width;
                            const parentWidth = parent.getBoundingClientRect().width;

                            if (elementWidth > 0 && parentWidth > 0) {
                                const rating = Math.round((elementWidth / parentWidth) * 5);

                                if (rating >= 1 && rating <= 5) {
                                    return rating;
                                }
                            }
                        }

                        return null;
                    }

                    const comments = Array.from(document.querySelectorAll("rz-comment"));

                    let injected = 0;

                    for (const comment of comments) {
                        const rating = parseRatingFromComment(comment);

                        if (rating !== null) {
                            comment.setAttribute("data-extracted-rating", String(rating));
                            injected += 1;
                        }
                    }

                    return injected;
                }
                """
            )

            print(f"[INFO] Browser injected ratings into {injected_count} review nodes")

            # Debug: save first comment HTML to understand what Playwright actually sees
            first_comment_html = page.evaluate(
                """
                () => {
                    const comment = document.querySelector("rz-comment");
                    return comment ? comment.outerHTML : "";
                }
                """
            )

            if first_comment_html:
                from pathlib import Path

                debug_dir = Path("data/debug")
                debug_dir.mkdir(parents=True, exist_ok=True)

                debug_path = debug_dir / "first_rozetka_comment.html"
                debug_path.write_text(first_comment_html, encoding="utf-8")

                print(f"[DEBUG] First comment HTML saved to: {debug_path}")

            html = page.content()
            return html

        finally:
            browser.close()


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def clean_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def first_text(node, selectors: Iterable[str]) -> Optional[str]:
    for selector in selectors:
        element = node.select_one(selector)

        if element:
            text = clean_text(element.get_text(" ", strip=True))

            if text:
                return text

    return None


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None

    match = re.search(r"-?\d+", value.replace(" ", ""))

    if not match:
        return None

    return int(match.group())


def review_key(review: Review) -> str:
    raw = "|".join(
        str(part or "")
        for part in [
            review.store,
            review.product_id,
            review.author,
            review.date,
            review.text,
        ]
    )

    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def dedupe_reviews(reviews: Iterable[Review]) -> List[Review]:
    seen = set()
    unique: List[Review] = []

    for review in reviews:
        key = review_key(review)

        if key not in seen:
            unique.append(review)
            seen.add(key)

    return unique


def save_reviews(reviews: List[Review], output_path: str, fmt: str = "json") -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [review.to_dict() for review in reviews]

    if fmt == "json":
        path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    elif fmt == "csv":
        pd.DataFrame(rows).to_csv(
            path,
            index=False,
            encoding="utf-8-sig",
        )

    else:
        raise ValueError("Unsupported format. Use 'json' or 'csv'.")