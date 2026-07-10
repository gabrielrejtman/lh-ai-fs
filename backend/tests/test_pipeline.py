import unittest
from pathlib import Path

from backend.agents import PromptConfig, build_verification_report
from backend.agents.citation_checker_agent import CitationCheckerAgent
from backend.run_evals import evaluate


class VerificationPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        documents_dir = Path(__file__).resolve().parents[1] / "documents"
        self.documents = {
            path.stem: path.read_text(encoding="utf-8")
            for path in documents_dir.glob("*.txt")
        }

    def test_build_verification_report_returns_structured_findings(self):
        report = build_verification_report(self.documents)

        self.assertIn("summary", report)
        self.assertIn("citations", report)
        self.assertIn("cross_document_findings", report)
        self.assertIn("quotes", report)
        self.assertGreaterEqual(len(report["citations"]), 1)
        self.assertGreaterEqual(len(report["cross_document_findings"]), 1)
        self.assertGreaterEqual(len(report["quotes"]), 1)
        self.assertEqual(report.get("status"), "ok")

    def test_quote_fidelity_flags_are_present(self):
        report = build_verification_report(self.documents)
        quote = report["quotes"][0]

        self.assertIn("quote_text", quote)
        self.assertIn("quote_fidelity", quote)
        self.assertIn(quote["quote_fidelity"], {"supported", "contradicted", "could_not_verify"})

    def test_orchestrator_handles_exceptions(self):
        broken_documents = {"motion_for_summary_judgment": None}
        report = build_verification_report(broken_documents)

        self.assertEqual(report.get("status"), "failed")
        self.assertEqual(report.get("confidence"), "low")
        self.assertIn("error", report)

    def test_citation_checker_accepts_confidence_labels(self):
        agent = CitationCheckerAgent()
        parsed = agent._parse_response(
            '{"citation":"Test citation","status":"supported","confidence":"high","reason":"Found explicit support","evidence":"The record says so."}',
            {"citation_text": "Test citation"},
        )

        self.assertEqual(parsed["status"], "supported")
        self.assertEqual(parsed["confidence"], "high")

    def test_build_verification_report_accepts_prompt_overrides(self):
        prompt_config = PromptConfig(overrides={"summary_agent_prompt": "Keep it brief."})
        report = build_verification_report(self.documents, prompt_config=prompt_config)

        self.assertIn("summary", report)
        self.assertIn("citations", report)

    def test_evaluate_penalizes_generic_citation_evidence(self):
        report = {
            "citations": [
                {
                    "citation": "Example v. Test",
                    "status": "could_not_verify",
                    "evidence": "No direct support found.",
                }
            ]
        }
        truth = {"citations": [{"citation": "Example v. Test", "status": "could_not_verify"}]}

        metrics = evaluate(report, truth)

        self.assertLess(metrics["citation_precision"], 1.0)
        self.assertLess(metrics["citation_recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
