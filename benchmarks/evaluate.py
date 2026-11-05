
import argparse
import json
from datetime import datetime
from pathlib import Path

from src.finance_council.market_data import MarketEvidence
from src.finance_council.valuation_agent import ValuationAssessment
from src.finance_council.risk_agent import RiskAssessment
from src.finance_council.momentum_agent import MomentumAssessment
from src.finance_council.council_graph import build_council_graph


ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "benchmarks" / "benchmark_dataset.json"
RESULTS_DIR = ROOT / "benchmarks" / "results"


ASSESSMENT_MODELS = {
    "valuation": ValuationAssessment,
    "risk": RiskAssessment,
    "momentum": MomentumAssessment,
}


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_assessment(name, assessment):
    if assessment is None:
        return False

    try:
        ASSESSMENT_MODELS[name].model_validate(assessment)
        return True
    except Exception:
        return False




def check_outlook_consistency(result):
    final_outlook = result.get("final_outlook")

    if not isinstance(final_outlook, dict):
        return False

    allowed_outlooks = {
        "positive",
        "negative",
        "mixed",
        "partial_directional",
        "insufficient_evidence",
    }

    overall = final_outlook.get("overall_outlook")

    if overall not in allowed_outlooks:
        return False

    dimensions = final_outlook.get("dimensions")

    if not isinstance(dimensions, dict):
        return False

    required_dimensions = {"valuation", "risk", "momentum"}

    if not required_dimensions.issubset(dimensions):
        return False

    allowed_dimension_values = {
        "positive",
        "negative",
        "neutral",
        "moderate",
        "high",
        "low",
        "insufficient_evidence",
        "failed",
    }

    return all(
        dimensions[name] in allowed_dimension_values
        for name in required_dimensions
    )



def serialize_assessment(assessment):
    if assessment is None:
        return None

    if hasattr(assessment, "model_dump"):
        return assessment.model_dump(mode="json")

    return assessment


def run_case(case, graph):
    ticker = case["ticker"]
    evidence = MarketEvidence.model_validate(case["market_evidence"])

    initial_state = {
        "evidence": evidence,
        "valuation": None,
        "risk": None,
        "momentum": None,
        "valuation_error": None,
        "risk_error": None,
        "momentum_error": None,
        "disagreement": None,
        "evidence_quality": None,
        "analytical_agreement": None,
        "execution_reliability": None,
        "final_outlook": None,
    }

    started_at = datetime.now().isoformat()

    try:
        result = graph.invoke(initial_state)

        assessment_validity = {
            name: validate_assessment(name, result.get(name))
            for name in ASSESSMENT_MODELS
        }

        execution_reliable = all(
            result.get(f"{name}_error") is None
            for name in ASSESSMENT_MODELS
        )

        consistency = check_outlook_consistency(result)

        return {
            "case_id": case["case_id"],
            "ticker": ticker,
            "scenario_category": case["scenario_category"],
            "started_at": started_at,
            "execution_reliable": execution_reliable,
            "assessment_validity": assessment_validity,
            "outlook_consistent": consistency,
            "agent_errors": {
                name: result.get(f"{name}_error")
                for name in ASSESSMENT_MODELS
            },
            "valuation": serialize_assessment(result.get("valuation")),
            "risk": serialize_assessment(result.get("risk")),
            "momentum": serialize_assessment(result.get("momentum")),
            "disagreement": serialize_assessment(result.get("disagreement")),
            "evidence_quality": serialize_assessment(
                result.get("evidence_quality")
            ),
            "analytical_agreement": serialize_assessment(
                result.get("analytical_agreement")
            ),
            "execution_reliability_report": serialize_assessment(
                result.get("execution_reliability")
            ),
            "final_outlook": result.get("final_outlook"),
            "error": None,
        }

    except Exception as error:
        return {
            "case_id": case["case_id"],
            "ticker": ticker,
            "scenario_category": case["scenario_category"],
            "started_at": started_at,
            "execution_reliable": False,
            "assessment_validity": {
                name: False for name in ASSESSMENT_MODELS
            },
            "outlook_consistent": False,
            "agent_errors": {},
            "valuation": None,
            "risk": None,
            "momentum": None,
            "disagreement": None,
            "evidence_quality": None,
            "analytical_agreement": None,
            "execution_reliability_report": None,
            "final_outlook": None,
            "error": str(error),
        }


def build_manual_review(results, cases):
    case_lookup = {
        case["case_id"]: case for case in cases
    }

    review_cases = []

    for result in results:
        original = case_lookup[result["case_id"]]

        review_cases.append({
            "case_id": result["case_id"],
            "ticker": result["ticker"],
            "scenario_category": result["scenario_category"],
            "expected_evidence_requirements": original.get(
                "expected_evidence_requirements", []
            ),
            "evaluation_notes": original.get("evaluation_notes", {}),
            "agent_outputs": {
                "valuation": result["valuation"],
                "risk": result["risk"],
                "momentum": result["momentum"],
            },
            "quality_reports": {
                "evidence_quality": result["evidence_quality"],
                "analytical_agreement": result["analytical_agreement"],
                "execution_reliability": result["execution_reliability_report"],
            },
            "automated_checks": {
                "execution_reliable": result["execution_reliable"],
                "assessment_validity": result["assessment_validity"],
                "outlook_consistent": result["outlook_consistent"],
            },
            "manual_scores": {
                "evidence_grounding": None,
                "unsupported_claims": None,
                "analytical_defensibility": None,
                "limitation_acknowledgment": None,
                "outlook_consistency": None,
            },
            "reviewer_justification": "",
            "critical_failure": False,
        })

    return {
        "evaluation_type": "manual_review",
        "scoring_scale": "0-5",
        "cases": review_cases,
    }


def summarize(results):
    total = len(results)

    reliable = sum(r["execution_reliable"] for r in results)
    valid = sum(
        all(r["assessment_validity"].values())
        for r in results
    )
    consistent = sum(r["outlook_consistent"] for r in results)

    return {
        "total_cases": total,
        "execution_reliable_cases": reliable,
        "execution_reliability_rate": reliable / total if total else 0,
        "fully_valid_cases": valid,
        "structured_output_validity_rate": valid / total if total else 0,
        "consistent_cases": consistent,
        "outlook_consistency_rate": consistent / total if total else 0,
        "agent_failure_count": sum(
            not r["execution_reliable"] for r in results
        ),
        "outer_execution_failure_count": sum(
            r["error"] is not None for r in results
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run live Finance Decision Council evaluation."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N benchmark cases.",
    )

    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="Run a specific benchmark case ID.",
    )

    args = parser.parse_args()

    dataset = load_dataset()
    cases = dataset["cases"]

    if args.case_id:
        cases = [
            case for case in cases
            if case["case_id"] == args.case_id
        ]

        if not cases:
            raise SystemExit(f"Unknown case ID: {args.case_id}")

    if args.limit:
        cases = cases[:args.limit]

    if not cases:
        raise SystemExit("No benchmark cases selected.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    graph = build_council_graph()

    results = []

    for index, case in enumerate(cases, start=1):
        print(
            f"\n[{index}/{len(cases)}] "
            f"Running {case['case_id']} ({case['ticker']})..."
        )

        result = run_case(case, graph)
        results.append(result)

        outlook = result.get("final_outlook") or {}
        print(f"  Outlook: {outlook.get('overall_outlook', 'ERROR')}")
        print(f"  Reliable: {result['execution_reliable']}")
        print(f"  Consistent: {result['outlook_consistent']}")

        if result["error"]:
            print(f"  ERROR: {result['error']}")

    summary = summarize(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results_path = RESULTS_DIR / f"evaluation_{timestamp}.json"
    review_path = RESULTS_DIR / f"manual_review_{timestamp}.json"

    evaluation_output = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "dataset_version": dataset.get("benchmark_version"),
        "inference_mode": "live",
        "summary": summary,
        "results": results,
    }

    review_output = build_manual_review(results, cases)

    with open(results_path, "w", encoding="utf-8") as file:
        json.dump(evaluation_output, file, indent=2)

    with open(review_path, "w", encoding="utf-8") as file:
        json.dump(review_output, file, indent=2)

    print("\nEvaluation Summary")
    print(json.dumps(summary, indent=2))

    print(f"\nResults saved: {results_path}")
    print(f"Manual review saved: {review_path}")


if __name__ == "__main__":
    main()
