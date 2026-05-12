class ReviewLLMClient:
    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self.model = model or os.getenv("LLM_MODEL", "gpt-4.1-mini")
        self.client = OpenAI(api_key=api_key)