import logging
from typing import Any

from .citation_checker_agent import CitationCheckerAgent
from .citation_extractor_agent import CitationExtractorAgent
from .cross_document_agent import CrossDocumentAgent
from .document_agent import DocumentAgent
from .quote_extractor_agent import QuoteExtractorAgent
from .summary_agent import SummaryAgent
from .schemas import PromptConfig

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, prompt_config: PromptConfig | None = None):
        self.prompt_config = prompt_config or PromptConfig()
        self.document_agent = DocumentAgent(prompt=self.prompt_config.get("document_agent_prompt", ""))
        self.quote_extractor = QuoteExtractorAgent(prompt=self.prompt_config.get("quote_extractor_prompt", ""))
        self.citation_extractor = CitationExtractorAgent(prompt=self.prompt_config.get("citation_extractor_prompt", ""))
        self.citation_checker = CitationCheckerAgent(prompt=self.prompt_config.get("citation_checker_prompt", ""))
        self.cross_document_agent = CrossDocumentAgent(prompt=self.prompt_config.get("cross_document_prompt", ""))
        self.summary_agent = SummaryAgent(prompt=self.prompt_config.get("summary_agent_prompt", ""))

    def run(self, documents: dict[str, str]) -> dict[str, Any]:
        try:
            normalized_documents = self.document_agent.run(documents)
            motion_text = normalized_documents.get("motion_for_summary_judgment", {}).get("text", "")

            quotes = self.quote_extractor.run(motion_text)
            citations = self.citation_extractor.run(motion_text)
            citation_results = self.citation_checker.run(citations, normalized_documents)
            cross_document_findings = self.cross_document_agent.run(normalized_documents)
            summary = self.summary_agent.run(citation_results, cross_document_findings, quotes)

            return {
                "summary": summary,
                "quotes": quotes,
                "citations": citation_results,
                "cross_document_findings": cross_document_findings,
                "document_count": len(normalized_documents),
                "confidence": self._calculate_confidence(citation_results, cross_document_findings, quotes),
                "status": "ok",
            }
        except Exception as exc:
            logger.exception("Orchestration failed")
            return {
                "summary": "The analysis failed due to an internal error.",
                "quotes": [],
                "citations": [],
                "cross_document_findings": [],
                "document_count": len(documents),
                "confidence": "low",
                "status": "failed",
                "error": str(exc),
            }

    def _calculate_confidence(self, citation_results: list[dict[str, Any]], cross_document_findings: list[dict[str, Any]], quotes: list[dict[str, Any]]) -> str:
        if not citation_results and not cross_document_findings and not quotes:
            return "medium"

        average = 0.0
        items = 0
        for result in citation_results + cross_document_findings + quotes:
            confidence = result.get("confidence")
            if isinstance(confidence, (int, float)):
                average += confidence
                items += 1
        if items == 0:
            return "medium"
        return "high" if average / items >= 0.8 else "medium" if average / items >= 0.6 else "low"
