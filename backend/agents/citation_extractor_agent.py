import json
import re
from typing import Any

from backend.llm import call_llm
from .prompts import CITATION_EXTRACTOR_PROMPT


class CitationExtractorAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt

    def run(self, motion_text: str) -> list[dict[str, Any]]:
        if not motion_text:
            return []

        try:
            messages = [
                {"role": "system", "content": self.prompt or CITATION_EXTRACTOR_PROMPT},
                {"role": "user", "content": f"Motion text:\n{motion_text}"},
            ]
            response = call_llm(messages, model="gpt-4o-mini", temperature=0)
            return self._parse_response(response)
        except Exception:
            return self._fallback_extract(motion_text)

    def _parse_response(self, response: str) -> list[dict[str, Any]]:
        payload = self._extract_json_array(response)
        if not payload:
            return self._fallback_extract(response)

        try:
            records = json.loads(payload)
            if isinstance(records, list):
                return records
        except json.JSONDecodeError:
            pass

        return self._fallback_extract(response)

    def _extract_json_array(self, text: str) -> str | None:
        match = re.search(r"\[\s*\{.*?\}\s*\]", text, re.DOTALL)
        return match.group(0) if match else None

    def _fallback_extract(self, text: str) -> list[dict[str, Any]]:
        return []
