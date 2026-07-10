import json
import re
from typing import Any

from backend.llm import call_llm
from .prompts import CROSS_DOCUMENT_PROMPT


class CrossDocumentAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt

    def run(self, normalized_documents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        motion = normalized_documents.get("motion_for_summary_judgment", {}).get("text", "")
        evidence_text = self._build_evidence_text(normalized_documents)

        if not motion:
            return []

        try:
            messages = [
                {"role": "system", "content": self.prompt or CROSS_DOCUMENT_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Motion text:\n{motion}\n\nSupporting documents:\n{evidence_text}"
                    ),
                },
            ]
            response = call_llm(messages, model="gpt-4o-mini", temperature=0)
            findings = self._parse_response(response)
            return findings
        except Exception:
            return [
                {
                    "issue": "cross_document_verification_failed",
                    "severity": "medium",
                    "summary": "The cross-document consistency review could not be completed because AI verification failed.",
                    "evidence": {},
                }
            ]

    def _build_evidence_text(self, normalized_documents: dict[str, dict[str, Any]]) -> str:
        parts: list[str] = []
        for name, doc in normalized_documents.items():
            if name == "motion_for_summary_judgment":
                continue
            text = doc.get("text", "")
            parts.append(f"--- {name} ---\n{text[:2500]}")
        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> list[dict[str, Any]]:
        payload = self._extract_json_array(response)
        if not payload:
            return []

        try:
            records = json.loads(payload)
            if isinstance(records, list):
                return records
        except json.JSONDecodeError:
            pass

        return []

    def _extract_json_array(self, text: str) -> str | None:
        match = re.search(r"\[\s*\{.*?\}\s*\]", text, re.DOTALL)
        return match.group(0) if match else None
