import json
import re
from typing import Any

from backend.llm import call_llm
from .prompts import CITATION_CHECKER_PROMPT


class CitationCheckerAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt

    def run(self, citations: list[dict[str, Any]], documents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        supporting_text = self._collect_evidence(documents)

        for citation in citations:
            try:
                messages = [
                    {"role": "system", "content": self.prompt or CITATION_CHECKER_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Citation: {citation.get('citation_text', '')}\n"
                            f"Quote snippet: {citation.get('quote_snippet', '')}\n"
                            f"Supporting documents:\n{supporting_text}"
                        ),
                    },
                ]
                response = call_llm(messages, model="gpt-4o-mini", temperature=0)
                parsed = self._parse_response(response, citation)
            except Exception:
                parsed = self._fallback_result(citation)

            results.append(parsed)

        return results

    def _collect_evidence(self, documents: dict[str, dict[str, Any]]) -> str:
        evidence_parts: list[str] = []
        for name, doc in documents.items():
            text = doc.get("text", "")
            evidence_parts.append(f"--- {name} ---\n{text[:2500]}")
        return "\n\n".join(evidence_parts)

    def _parse_response(self, response: str, citation: dict[str, Any]) -> dict[str, Any]:
        payload = self._extract_json_object(response)
        if not payload:
            return self._fallback_result(citation)

        try:
            parsed = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            return self._fallback_result(citation)

        return {
            "citation": parsed.get("citation", citation.get("citation_text", "")),
            "status": parsed.get("status", "could_not_verify"),
            "confidence": float(parsed.get("confidence", 0.6)),
            "reason": parsed.get("reason", "Unable to verify the citation from the available evidence."),
            "evidence": parsed.get("evidence", citation.get("quote_snippet", "")),
        }

    def _extract_json_object(self, text: str) -> str | None:
        cleaned = text.strip()

        # Remove common markdown/quote wrappers
        if cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned[3:-3].strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                json.loads(cleaned)
                return cleaned
            except json.JSONDecodeError:
                pass

        # Find the first valid JSON object by brace matching.
        start = None
        level = 0
        for index, char in enumerate(cleaned):
            if char == "{":
                if level == 0:
                    start = index
                level += 1
            elif char == "}":
                level -= 1
                if level == 0 and start is not None:
                    candidate = cleaned[start : index + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        start = None
        return None

    def _fallback_result(self, citation: dict[str, Any]) -> dict[str, Any]:
        return {
            "citation": citation.get("citation_text", ""),
            "status": "could_not_verify",
            "confidence": 0.0,
            "reason": "AI verification was unavailable or returned an unparsable response.",
            "evidence": citation.get("quote_snippet", ""),
        }
