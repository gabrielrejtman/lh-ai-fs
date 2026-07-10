import json
from typing import Any
from pydantic import BaseModel
from backend.llm import call_llm_structured
from .prompts import SUMMARY_AGENT_PROMPT

class SummaryResult(BaseModel):
    executive_summary: str
    critical_flaws_count: int
    unverified_claims_count: int
    key_warnings: list[str]

class SummaryAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt or SUMMARY_AGENT_PROMPT

    def run(
        self,
        citation_results: list[dict[str, Any]],
        cross_document_findings: list[dict[str, Any]],
        quotes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        
        # Consolidates the output of the earlier agents for the summary
        context_payload = {
            "citations": citation_results,
            "cross_document_findings": cross_document_findings,
            "quotes": quotes
        }

        try:
            messages = [
                {"role": "system", "content": self.prompt},
                {
                    "role": "user", 
                    "content": f"Raw verification data to summarize:\n{json.dumps(context_payload)}"
                },
            ]
            
            parsed_result = call_llm_structured(
                messages=messages,
                response_model=SummaryResult,
                model="gpt-4o",  # The summary requires more reasoning, so gpt-4o is ideal; use the mini model if you want to save cost
                temperature=0
            )
            
            return parsed_result.model_dump()
            
        except Exception as exc:
            print(f"Summary generation failed: {exc}")
            return {
                "executive_summary": "System failed to generate an executive summary.",
                "critical_flaws_count": 0,
                "unverified_claims_count": 0,
                "key_warnings": ["Summary agent encountered an API error."]
            }