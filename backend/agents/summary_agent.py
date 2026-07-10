from typing import Any


class SummaryAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt

    def run(
        self,
        citation_results: list[dict[str, Any]],
        cross_document_findings: list[dict[str, Any]],
        quotes: list[dict[str, Any]],
    ) -> str:
        if not citation_results and not cross_document_findings and not quotes:
            return "No material issues were identified in the supplied case materials."

        issue_count = len(citation_results) + len(cross_document_findings) + len(quotes)
        high_severity = [finding for finding in cross_document_findings if finding.get("severity") == "high"]
        return (
            f"The review identified {issue_count} discrete review points across citations, quote fidelity checks, and document consistency checks. "
            f"{len(high_severity)} findings were marked high severity, and the overall record suggests material inconsistency between the motion and the supporting evidence."
        )
