import json
import os
from datetime import datetime

from core.logic_isolation_test import SentinelTester
from core.ROUGE_scores import calculate_rouge_scores
from core.response_utils import parse_audit_response, validate_audit_schema


def main():
    print("🛡️  Starting Sentinel Thread: Adversarial Red Teaming...")

    # 1. Initialize tester and paths
    tester = SentinelTester()
    payload_path = os.path.join("payloads", "email_scenarios.json")

    # 2. Load test cases
    with open(payload_path, "r") as f:
        scenarios = json.load(f)

    # 3. Execution Loop (batch scenarios)
    results = []
    for case in scenarios:
        print(f"\n[Running {case['case_id']}] - {case['description']}")

        raw_output = tester.run_test(case["email_thread"])
        parsed_output, clean_output = parse_audit_response(raw_output)
        schema_validation = validate_audit_schema(parsed_output)
        reference_answer = case.get("reference_answer", case["email_thread"])
        expected_is_inclusive = case.get("expected_is_inclusive")
        prediction_match = None
        if isinstance(expected_is_inclusive, bool):
            prediction_match = (
                parsed_output.get("is_inclusive") == expected_is_inclusive
            )

        print(f"--- 🤖 Model Response ---")
        print(clean_output)
        print("--- ✅ Parsed Audit ---")
        print(json.dumps(parsed_output, ensure_ascii=False, indent=2))
        print(
            f"--- 🧪 Schema Validation ---\n"
            f"valid={schema_validation['is_valid']}, "
            f"errors={schema_validation['errors']}"
        )

        rouge_scores = calculate_rouge_scores(reference_answer, clean_output)
        print("--- 📊 ROUGE Scores ---")
        for metric, values in rouge_scores.items():
            print(
                f"{metric}: P={values.precision:.2f}, "
                f"R={values.recall:.2f}, F1={values.fmeasure:.2f}"
            )
        if prediction_match is not None:
            print("--- 🎯 Label Match ---")
            print(
                f"expected_is_inclusive={expected_is_inclusive}, "
                f"predicted_is_inclusive={parsed_output.get('is_inclusive')}, "
                f"match={prediction_match}"
            )

        results.append(
            {
                "case_id": case["case_id"],
                "description": case["description"],
                "parsed_output": parsed_output,
                "schema_validation": schema_validation,
                "expected_is_inclusive": expected_is_inclusive,
                "prediction_match": prediction_match,
                "rouge": {
                    metric: {
                        "precision": round(values.precision, 4),
                        "recall": round(values.recall, 4),
                        "f1": round(values.fmeasure, 4),
                    }
                    for metric, values in rouge_scores.items()
                },
            }
        )
        print("-" * 30)

    os.makedirs("reports", exist_ok=True)
    os.makedirs(os.path.join("reports", "runs"), exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_report_path = os.path.join("reports", "runs", f"{timestamp}.json")
    latest_report_path = os.path.join("reports", "latest.json")
    compatible_report_path = os.path.join("reports", "evaluation_results.json")

    with open(run_report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(latest_report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Backward-compatible output path used by current tooling/docs.
    with open(compatible_report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🧾 Run report: {run_report_path}")
    print(f"🧾 Latest report: {latest_report_path}")
    print(f"🧾 Compatible report: {compatible_report_path}")
    print("\n✅ All Red Team scenarios completed.")


if __name__ == "__main__":
    main()
