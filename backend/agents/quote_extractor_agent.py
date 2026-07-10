from typing import Any, Literal
from pydantic import BaseModel
from backend.llm import call_llm_structured
from .prompts import QUOTE_EXTRACTOR_PROMPT

class QuoteRecord(BaseModel):
    quote_text: str
    source: str
    quote_snippet: str
    quote_fidelity: Literal["supported", "contradicted", "could_not_verify"]
    confidence: Literal["high", "medium", "low"]
    reason: str

class QuoteExtractionResult(BaseModel):
    quotes: list[QuoteRecord]

class QuoteExtractorAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt or QUOTE_EXTRACTOR_PROMPT

    def run(self, motion_text: str) -> list[dict[str, Any]]:
        if not motion_text:
            return []

        try:
            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": f"Motion text:\n{motion_text}"},
            ]
            
            parsed_result = call_llm_structured(
                messages=messages,
                response_model=QuoteExtractionResult,
                model="gpt-4o-mini",
                temperature=0
            )
            
            return [quote.model_dump() for quote in parsed_result.quotes]
            
        except Exception as exc:
            print(f"Quote extraction failed: {exc}")
            return []