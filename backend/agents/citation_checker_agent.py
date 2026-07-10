from typing import Any, Literal
from pydantic import BaseModel
from backend.llm import call_llm_structured
from .prompts import CITATION_CHECKER_PROMPT

class CitationVerificationResult(BaseModel):
    citation: str
    status: Literal["supported", "contradicted", "could_not_verify"]
    confidence: Literal["high", "medium", "low"]
    reason: str
    evidence: str

class CitationCheckerAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt or CITATION_CHECKER_PROMPT

    def run(self, citations: list[dict[str, Any]], documents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        
        # Critical fix: passing the full document without slicing
        supporting_text = self._collect_full_evidence(documents)

        for citation in citations:
            try:
                messages = [
                    {"role": "system", "content": self.prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Citation: {citation.get('citation_text', '')}\n"
                            f"Quote snippet: {citation.get('quote_snippet', '')}\n"
                            f"Supporting documents:\n{supporting_text}"
                        ),
                    },
                ]
                
                # 2. The magic happens here: the response already comes back typed and validated
                parsed_result = call_llm_structured(
                    messages=messages,
                    response_model=CitationVerificationResult,
                    model="gpt-4o",
                    temperature=0
                )
                
                # Converting the Pydantic model back to a dict for the rest of the pipeline
                results.append(parsed_result.model_dump())
                
            except Exception as exc:
                # Pydantic raises ValidationError if the LLM hallucinates the structure
                print(f"Agent verification failed: {exc}") 
                results.append(self._fallback_result(citation))

        return results

    def _collect_full_evidence(self, documents: dict[str, dict[str, Any]]) -> str:
        evidence_parts: list[str] = []
        for name, doc in documents.items():
            text = doc.get("text", "")
            # REMOVIDO o text[:2500] que corria o risco de ocultar provas cruciais
            evidence_parts.append(f"--- {name} ---\n{text}")
        return "\n\n".join(evidence_parts)

    def _fallback_result(self, citation: dict[str, Any]) -> dict[str, Any]:
        return {
            "citation": citation.get("citation_text", ""),
            "status": "could_not_verify",
            "confidence": "low",
            "reason": "AI verification was unavailable or structural validation failed.",
            "evidence": citation.get("quote_snippet", ""),
        }