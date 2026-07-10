from backend.run_evals import load_documents, build_ground_truth, evaluate, build_verification_report


def main() -> None:
    documents = load_documents()
    report = build_verification_report(documents)
    truth = build_ground_truth()
    metrics = evaluate(report, truth)

    print("Evaluation metrics:")
    for name, value in metrics.items():
        print(f"- {name}: {value:.2f}")

    print("\nFull report and metrics written to backend/eval_results.json")


if __name__ == "__main__":
    main()
