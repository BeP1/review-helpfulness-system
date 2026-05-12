from __future__ import annotations

import argparse

from src.review_parser.parsers.factory import get_parser_for_url
from src.review_parser.utils import save_reviews


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Parse product reviews from supported online stores.")
    arg_parser.add_argument("url", help="Product or reviews URL")
    arg_parser.add_argument("--out", default="data/reviews.json", help="Output path")
    arg_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    arg_parser.add_argument("--max-pages", type=int, default=1, help="Max review pages to parse")
    args = arg_parser.parse_args()

    parser = get_parser_for_url(args.url)
    reviews = parser.parse(args.url, max_pages=args.max_pages)
    save_reviews(reviews, args.out, fmt=args.format)

    print(f"Store: {parser.store_name}")
    print(f"Reviews parsed: {len(reviews)}")
    print(f"Saved to: {args.out}")


if __name__ == "__main__":
    main()
