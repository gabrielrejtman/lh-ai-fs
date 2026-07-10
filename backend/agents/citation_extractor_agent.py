from typing import Any
from pydantic import BaseModel
from backend.llm import call_llm_structured
from .prompts import CITATION_EXTRACTOR_PROMPT

class CitationRecord(BaseModel):
    citation_text: str
    case_name: str | None
    kind: str
    source: str
    quote_snippet: str

class CitationExtractionResult(BaseModel):
    citations: list[CitationRecord]

class CitationExtractorAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt or CITATION_EXTRACTOR_PROMPT

    def run(self, motion_text: str) -> list[dict[str, Any]]:
        if not motion_text:
            return []

        try:
            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": f"Motion text:\n{motion_text}"},
            ]
            
            # 2. Calling OpenAI while forcing the response to be a valid list of citations
            parsed_result = call_llm_structured(
                messages=messages,
                response_model=CitationExtractionResult,
                model="gpt-4o-mini",
                temperature=0
            )
            
            # 3. Returning the validated list converted back to dictionaries
            return [record.model_dump() for record in parsed_result.citations]
            
        except Exception as exc:
            print(f"Agent extraction failed: {exc}")
            return self._fallback_extract()

    def _fallback_extract(self) -> list[dict[str, Any]]:
        return []