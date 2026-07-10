import json
from pathlib import Path

from backend.agents import PromptConfig, build_verification_report


def load_documents() -> dict[str, str]:
    root = Path(__file__).resolve().parent
    documents = {}
    for path in (root / "documents").glob("*.txt"):
        documents[path.stem] = path.read_text(encoding="utf-8")
    return documents


def build_ground_truth() -> dict[str, list[dict[str, str]]]:
    return {
        "citations": [
            {
                "citation": "Privette v. Superior Court, 5 Cal.4th 689 (1993)",
                "status": "potentially_misstated",
            },
            {
                "citation": "Seabright Insurance Co. v. US Airways, Inc., 52 Cal.4th 590 (2011)",
                "status": "could_not_verify",
            },
        ],
        "quotes": [
            {
                "quote_text": "A hirer is never liable for injuries sustained by an independent contractor's employees when the injuries arise from the contracted work.",
                "quote_fidelity": "could_not_verify",
            }
        ],
        "cross_document_findings": [
            {
                "issue": "date_mismatch",
                "severity": "high",
            },
            {
                "issue": "ppe_contradiction",
                "severity": "high",
            },
        ],
    }


def evaluate(report: dict[str, list[dict[str, str]]], truth: dict[str, list[dict[str, str]]]) -> dict[str, float]:
    metrics = {}

    def score_section(section: str, key: str) -> tuple[float, float, float]:
        predicted = report.get(section, [])
        expected = truth.get(section, [])
        if not expected:
            return 1.0, 1.0, 0.0

        correct = 0
        false_positives = 0
        hallucinations = 0
        matched = set()

        for predicted_item in predicted:
            expected_match = next(
                (
                    expected_item
                    for expected_item in expected
                    if expected_item[key] == predicted_item.get(key)
                ),
                None,
            )
            if expected_match:
                matched.add(expected_match[key])
                if all(predicted_item.get(field) == expected_match.get(field) for field in expected_match if field != key):
                    correct += 1
                else:
                    false_positives += 1
            else:
                hallucinations += 1

        precision = correct / max(correct + false_positives + hallucinations, 1)
        recall = correct / len(expected)
        hallucination_rate = hallucinations / max(len(predicted), 1)
        return precision, recall, hallucination_rate

    citation_metrics = score_section("citations", "citation")
    quote_metrics = score_section("quotes", "quote_text")
    cross_doc_metrics = score_section("cross_document_findings", "issue")

    metrics["citation_precision"] = citation_metrics[0]
    metrics["citation_recall"] = citation_metrics[1]
    metrics["citation_hallucination_rate"] = citation_metrics[2]
    metrics["quote_precision"] = quote_metrics[0]
    metrics["quote_recall"] = quote_metrics[1]
    metrics["quote_hallucination_rate"] = quote_metrics[2]
    metrics["cross_document_precision"] = cross_doc_metrics[0]
    metrics["cross_document_recall"] = cross_doc_metrics[1]
    metrics["cross_document_hallucination_rate"] = cross_doc_metrics[2]

    return metrics


if __name__ == "__main__":
    documents = load_documents()
    report = build_verification_report(documents)
    truth = build_ground_truth()
    metrics = evaluate(report, truth)

    print("Evaluation metrics:")
    for name, value in metrics.items():
        print(f"- {name}: {value:.2f}")

    output = {
        "report": report,
        "metrics": metrics,
    }
    print("\nFull report and metrics written to backend/eval_results.json")
    with open(Path(__file__).resolve().parent / "eval_results.json", "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)
