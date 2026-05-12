from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

from .models import Review


UA_RU_MONTHS = (
    "січня|лютого|березня|квітня|травня|червня|липня|серпня|"
    "вересня|жовтня|листопада|грудня|"
    "января|февраля|марта|апреля|мая|июня|июля|августа|"
    "сентября|октября|ноября|декабря"
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
    "Referer": "https://rozetka.com.ua/ua/",
}


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def select_text(node, selector: str) -> Optional[str]:
    element = node.select_one(selector)

    if not element:
        return None

    return clean_text(element.get_text(" ", strip=True))


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None

    match = re.search(r"-?\d+", value.replace(" ", ""))

    if not match:
        return None

    return int(match.group())


def fetch_html(
    url: str,
    delay_sec: float = 0.7,
    timeout: int = 30,
    use_browser: bool = False,
) -> str:
    if use_browser:
        return fetch_html_with_browser(url=url, timeout=timeout)

    time.sleep(delay_sec)

    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.text
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None

        if status_code in {403, 429}:
            return fetch_html_with_browser(url=url, timeout=timeout)

        raise


def fetch_html_with_browser(url: str, timeout: int = 30) -> str:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: "
            "pip install playwright && python -m playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="uk-UA",
            timezone_id="Europe/Kyiv",
            viewport={"width": 1366, "height": 900},
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

            try:
                page.wait_for_selector("rz-comment", timeout=timeout * 1000)
            except PlaywrightTimeoutError:
                return page.content()

            for _ in range(8):
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(400)

            inject_rozetka_ratings(page)

            return page.content()
        finally:
            browser.close()


def inject_rozetka_ratings(page) -> None:
    page.evaluate(
        """
        () => {
            function parseRatingFromStyle(style) {
                if (!style) {
                    return null;
                }

                const calcMatch = style.match(
                    /width\\s*:\\s*calc\\(\\s*(\\d+(?:[\\.,]\\d+)?)%\\s*-/i
                );

                if (calcMatch) {
                    const percent = parseFloat(calcMatch[1].replace(",", "."));
                    const rating = Math.round(percent / 20);

                    if (rating >= 1 && rating <= 5) {
                        return rating;
                    }
                }

                const percentMatch = style.match(
                    /width\\s*:\\s*(\\d+(?:[\\.,]\\d+)?)\\s*%/i
                );

                if (percentMatch) {
                    const percent = parseFloat(percentMatch[1].replace(",", "."));
                    const rating = Math.round(percent / 20);

                    if (rating >= 1 && rating <= 5) {
                        return rating;
                    }
                }

                return null;
            }

            const comments = Array.from(document.querySelectorAll("rz-comment"));

            for (const comment of comments) {
                const existing = comment.getAttribute("data-extracted-rating");

                if (existing) {
                    continue;
                }

                const ratingElement = comment.querySelector('[data-testid="stars-rating"]');

                if (!ratingElement) {
                    continue;
                }

                const rating = parseRatingFromStyle(
                    ratingElement.getAttribute("style") || ""
                );

                if (rating !== null) {
                    comment.setAttribute("data-extracted-rating", String(rating));
                }
            }
        }
        """
    )

def review_key(review: Review) -> str:
    raw = "|".join(
        str(part or "")
        for part in [
            review.store,
            review.product_id,
            review.author,
            review.date,
            review.text,
            review.pros,
            review.cons,
        ]
    )

    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def dedupe_reviews(reviews: Iterable[Review]) -> list[Review]:
    seen = set()
    result: list[Review] = []

    for review in reviews:
        key = review_key(review)

        if key in seen:
            continue

        seen.add(key)
        result.append(review)

    return result