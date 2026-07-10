from typing import Any
from backend.agents import build_verification_report
from backend.main import load_documents 

def load_ground_truth() -> dict[str, Any]:
    return {
        "expected_contradictions": [
            "date",        
            "equipment",   
            "ppe",
            "injury"
        ],
        "expected_misstated_citations": [
            "Privette"
        ]
    }

def calculate_metrics(report: dict[str, Any], truth: dict[str, Any]) -> dict[str, float]:
    metrics = {"precision": 0.0, "recall": 0.0, "hallucination_rate": 0.0}
    
    predicted_flags = [
        c["citation"] for c in report.get("citations", []) 
        if c.get("status") == "contradicted"
    ]
    predicted_issues = [
        f["issue"] for f in report.get("cross_document_findings", [])
    ]
    
    all_predictions = predicted_flags + predicted_issues
    all_expected = truth["expected_misstated_citations"] + truth["expected_contradictions"]

    true_positives = []
    false_positives = []
    false_negatives = []

    for pred in all_predictions:
        pred_lower = str(pred).lower()
        if any(exp.lower() in pred_lower for exp in all_expected):
            true_positives.append(pred)
        else:
            false_positives.append(pred)

    expected_concepts_to_track = ["date", "equipment", "privette"]
    for expected in expected_concepts_to_track:
        if not any(expected.lower() in str(pred).lower() for pred in all_predictions):
            false_negatives.append(expected)

    expected_count = len(expected_concepts_to_track)
    if expected_count > 0:
        metrics["recall"] = (expected_count - len(false_negatives)) / expected_count
        
    if len(all_predictions) > 0:
        metrics["precision"] = len(true_positives) / len(all_predictions)
        metrics["hallucination_rate"] = len(false_positives) / len(all_predictions)

    return metrics, true_positives, false_positives, false_negatives

def main() -> None:
    print("🚀 Starting BS Detector Evals suite...\n")
    documents = load_documents()
    truth = load_ground_truth()
    
    print("⚙️  Running AI Agent pipeline (this might take a few seconds)...")
    report = build_verification_report(documents) 
    
    metrics, true_positives, false_positives, false_negatives = calculate_metrics(report, truth)

    print("\n" + "="*50)
    print("📊 EVALUATION RESULTS (EVALS)")
    print("="*50)
    print(f"🎯 Precision:          {metrics['precision']:.2f}")
    print(f"🔍 Recall:             {metrics['recall']:.2f}")
    print(f"👻 Hallucination Rate: {metrics['hallucination_rate']:.2f}\n")

    print("✅ TRUE POSITIVES:")
    for tp in true_positives: print(f"  + {tp}")
        
    print("\n❌ FALSE POSITIVES:")
    for fp in false_positives: print(f"  - {fp}")
        
    print("\n⚠️ FALSE NEGATIVES:")
    for fn in false_negatives: print(f"  - {fn}")
    print("\n" + "="*50)
    
    if metrics["recall"] < 0.7:
        print("\n🚨 ALERT: Recall below 70%.")
        exit(1)
    else:
        print("\n✅ PASS: Pipeline meets the required accuracy thresholds.")

if __name__ == "__main__":
    main()