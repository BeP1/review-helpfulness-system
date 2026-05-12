import json
import os
from typing import Any
from openai import OpenAI
from .prompts import SYSTEM_PROMPT
from .schemas import HELPFULNESS_SCHEMA
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


class ReviewLLMClient:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("LLM_MODEL", "gpt-5.4-mini")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "review_helpfulness_analysis",
                    "schema": HELPFULNESS_SCHEMA,
                    "strict": True,
                }
            },
        )

        return json.loads(response.output_text)