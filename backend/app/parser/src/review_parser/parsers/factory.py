from __future__ import annotations

from typing import List

from ..base import BaseParser
from .generic_jsonld import GenericJsonLdParser
from .rozetka import RozetkaParser


def get_parsers() -> List[BaseParser]:
    return [
        RozetkaParser(),
        GenericJsonLdParser(),
    ]


def get_parser_for_url(url: str) -> BaseParser:
    for parser in get_parsers():
        if parser.can_parse(url):
            return parser
    raise ValueError(f"No parser found for URL: {url}")
