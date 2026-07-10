import json
import re
from typing import Any

from backend.llm import call_llm
from .prompts import QUOTE_EXTRACTOR_PROMPT


class QuoteExtractorAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt

    def run(self, motion_text: str) -> list[dict[str, Any]]:
        if not motion_text:
            return []

        try:
            messages = [
                {"role": "system", "content": self.prompt or QUOTE_EXTRACTOR_PROMPT},
                {"role": "user", "content": f"Motion text:\n{motion_text}"},
            ]
            response = call_llm(messages, model="gpt-4o-mini", temperature=0)
            return self._parse_response(response)
        except Exception:
            return self._fallback_quotes(motion_text)

    def _parse_response(self, response: str) -> list[dict[str, Any]]:
        payload = self._extract_json_payload(response)
        if not payload:
            return self._fallback_quotes(response)

        try:
            records = json.loads(payload)
            if isinstance(records, dict) and "quotes" in records and isinstance(records["quotes"], list):
                records = records["quotes"]
            if isinstance(records, dict):
                records = [records]
            if isinstance(records, list):
                normalized_records = [self._normalize_record(record) for record in records if isinstance(record, dict)]
                if normalized_records:
                    return normalized_records
        except json.JSONDecodeError:
            pass

        return self._fallback_quotes(response)

    def _extract_json_payload(self, text: str) -> str | None:
        try:
            parsed = json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
        if match:
            return match.group(0)

        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else None

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "quote_text": record.get("quote_text") or record.get("quote") or record.get("text"),
            "source": record.get("source", "motion"),
            "quote_snippet": record.get("quote_snippet") or record.get("context") or record.get("quote_context", ""),
            "quote_fidelity": self._normalize_fidelity(
                record.get("quote_fidelity") or record.get("fidelity_assessment") or record.get("fidelity", "could_not_verify")
            ),
            "confidence": self._normalize_confidence(record.get("confidence")),
            "reason": record.get("reason") or record.get("explanatory_reason") or "AI quote extraction result.",
        }
        return normalized

    def _normalize_fidelity(self, value: Any) -> str:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"supported", "contradicted", "could_not_verify"}:
                return normalized
            if normalized in {"high", "medium", "low", "strong", "weak", "uncertain"}:
                return "could_not_verify"
        return "could_not_verify"

    def _normalize_confidence(self, value: Any) -> float:
        if isinstance(value, str):
            try:
                return float(value.strip('%')) / 100 if '%' in value else float(value)
            except ValueError:
                return 0.6
        if isinstance(value, (int, float)):
            return float(value)
        return 0.6

    def _fallback_quotes(self, text: str) -> list[dict[str, Any]]:
        pattern = re.compile(r'[“"]([^”"]{20,500})[”"]')
        quotes: list[dict[str, Any]] = []
        for match in pattern.finditer(text):
            quotes.append(
                {
                    "quote_text": match.group(1).strip(),
                    "source": "motion",
                    "quote_snippet": self._extract_context(text, match.start(), match.end()),
                    "quote_fidelity": "could_not_verify",
                    "confidence": 0.58,
                    "reason": "Fallback quote extraction used when AI verification was unavailable.",
                }
            )
        return quotes

    def _extract_context(self, text: str, start: int, end: int, radius: int = 120) -> str:
        start_idx = max(0, start - radius)
        end_idx = min(len(text), end + radius)
        return text[start_idx:end_idx].replace("\n", " ").strip()
