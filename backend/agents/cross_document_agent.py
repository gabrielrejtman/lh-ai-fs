from typing import Any, Literal
from pydantic import BaseModel
from backend.llm import call_llm_structured
from .prompts import CROSS_DOCUMENT_PROMPT

# 1. Definindo os Contratos de Dados
class Finding(BaseModel):
    issue: str
    severity: Literal["critical", "minor"]
    summary: str
    evidence: str

class CrossDocumentResult(BaseModel):
    findings: list[Finding]

class CrossDocumentAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt or CROSS_DOCUMENT_PROMPT

    def run(self, normalized_documents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        motion = normalized_documents.get("motion_for_summary_judgment", {}).get("text", "")
        evidence_text = self._build_full_evidence_text(normalized_documents)

        if not motion:
            return []

        try:
            messages = [
                {"role": "system", "content": self.prompt},
                {
                    "role": "user",
                    "content": f"Motion text:\n{motion}\n\nSupporting documents:\n{evidence_text}",
                },
            ]
            
            parsed_result = call_llm_structured(
                messages=messages,
                response_model=CrossDocumentResult,
                model="gpt-4o",
                temperature=0
            )
            
            return [finding.model_dump() for finding in parsed_result.findings]
            
        except Exception as exc:
            print(f"Cross-document verification failed: {exc}")
            return [
                {
                    "issue": "cross_document_verification_failed",
                    "severity": "minor",
                    "summary": "The consistency review could not be completed.",
                    "evidence": "",
                }
            ]

    def _build_full_evidence_text(self, normalized_documents: dict[str, dict[str, Any]]) -> str:
        parts: list[str] = []
        for name, doc in normalized_documents.items():
            if name == "motion_for_summary_judgment":
                continue
            text = doc.get("text", "")
            # REMOVIDO o corte de 2500 caracteres
            parts.append(f"--- {name} ---\n{text}")
        return "\n\n".join(parts)