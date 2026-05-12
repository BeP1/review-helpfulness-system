from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .models import Review


class BaseParser(ABC):
    store_name: str = "base"

    @abstractmethod
    def can_parse(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, url: str, max_pages: int = 1) -> List[Review]:
        raise NotImplementedError
