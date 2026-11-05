
import copy
import json
from pathlib import Path

RAW_PATH = Path(__file__).parent / "market_evidence.json"
OUTPUT_PATH = Path(__file__).parent / "benchmark_dataset.json"


def load_cases():
    data = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    return {case["ticker"]: case for case in data["cases"]}


def assign_case(case, category, valuation, risk, momentum, acceptable, unacceptable, limitations):
    case = copy.deepcopy(case)
    case["scenario_category"] = category
    case["expected_evidence_requirements"] = {
        "valuation": valuation,
        "risk": risk,
        "momentum": momentum,
    }
    case["evaluation_notes"] = {
        "acceptable_conclusions": acceptable,
        "unacceptable_claims": unacceptable,
        "limitations_to_acknowledge": limitations,
    }
    return case


def mask_fields(case, fields):
    case = copy.deepcopy(case)
    evidence = case["market_evidence"]

    for field in fields:
        evidence[field] = None

    evidence["missing_fields"] = sorted(
        set(evidence["missing_fields"]) | set(fields)
    )

    return case


def main():
    raw = load_cases()
    benchmark_cases = []

    # Positive / constructive evidence
    benchmark_cases.append(assign_case(
        raw["AAPL"],
        "positive",
        ["P/E and P/B indicate valuation sensitivity"],
        ["Beta indicates moderate market sensitivity"],
        ["Price above MA20, MA50, and MA200; positive 20d and 50d returns"],
        ["Constructive historical momentum with valuation caution"],
        ["Guaranteed future appreciation", "Undocumented peer valuation claims"],
        ["No peer benchmarks or forward earnings estimates"],
    ))

    benchmark_cases.append(assign_case(
        raw["MSFT"],
        "positive",
        ["P/E provides valuation context but no standalone fair value"],
        ["Beta indicates market sensitivity"],
        ["Price above moving averages; positive 20d and 50d returns"],
        ["Constructive historical momentum"],
        ["Guaranteed future appreciation"],
        ["No peer or historical valuation benchmark"],
    ))

    benchmark_cases.append(assign_case(
        raw["KO"],
        "positive",
        ["P/E requires contextual comparison"],
        ["Low beta indicates lower historical market sensitivity; D/E requires industry context"],
        ["Positive 20d and 50d returns; price above moving averages"],
        ["Constructive historical momentum with contextual risk"],
        ["Claiming low beta means no risk"],
        ["No peer benchmark; leverage interpretation is industry-dependent"],
    ))

    # Negative / deteriorating momentum evidence
    benchmark_cases.append(assign_case(
        raw["GOOGL"],
        "negative",
        ["P/E alone does not establish undervaluation"],
        ["Beta indicates market sensitivity"],
        ["Negative 20d and 50d returns; price below moving averages"],
        ["Deteriorating historical momentum"],
        ["Claiming price decline guarantees future losses"],
        ["No causal explanation for price decline"],
    ))

    benchmark_cases.append(assign_case(
        raw["INTC"],
        "negative",
        ["P/E is missing and cannot be assessed"],
        ["High beta indicates substantial historical market sensitivity"],
        ["Strongly negative 20d and 50d returns; price below moving averages"],
        ["Deteriorating momentum with valuation evidence gap"],
        ["Inventing P/E or fair value"],
        ["Missing P/E; no causal explanation for price decline"],
    ))

    # Mixed evidence
    benchmark_cases.append(assign_case(
        raw["META"],
        "neutral",
        ["P/E requires contextual comparison"],
        ["Beta indicates market sensitivity"],
        ["Negative 20d return but positive 50d return; price near/below MA200"],
        ["Mixed momentum across time horizons"],
        ["Treating either time horizon as conclusive"],
        ["No causal explanation or peer benchmark"],
    ))

    benchmark_cases.append(assign_case(
        raw["JPM"],
        "neutral",
        ["P/E available; EV/EBITDA and D/E missing"],
        ["Beta indicates market sensitivity"],
        ["Positive 20d return but slightly negative 50d return"],
        ["Mixed momentum and incomplete financial evidence"],
        ["Inventing missing leverage or EV/EBITDA values"],
        ["Missing D/E and EV/EBITDA"],
    ))

    # Insufficient evidence cases: intentionally masked snapshots
    nvda = mask_fields(raw["NVDA"], ["trailing_pe", "price_to_book"])
    benchmark_cases.append(assign_case(
        nvda,
        "insufficient_evidence",
        ["P/E and P/B are unavailable in this case"],
        ["Beta indicates elevated market sensitivity"],
        ["Negative 20d and 50d returns; price below MA20 and MA200"],
        ["Momentum can be assessed; valuation assessment must acknowledge missing metrics"],
        ["Inventing missing valuation ratios"],
        ["Masked valuation metrics; no peer benchmarks"],
    ))

    amzn = mask_fields(raw["AMZN"], [
        "trailing_pe",
        "price_to_book",
        "enterprise_to_ebitda",
    ])
    benchmark_cases.append(assign_case(
        amzn,
        "insufficient_evidence",
        ["All selected valuation ratios are unavailable"],
        ["Beta indicates market sensitivity"],
        ["Positive but modest 20d and 50d returns"],
        ["Valuation insufficient evidence; momentum remains assessable"],
        ["Claiming valuation is cheap or expensive"],
        ["Masked valuation metrics"],
    ))

    tsla = mask_fields(raw["TSLA"], [
        "trailing_pe",
        "price_to_book",
        "enterprise_to_ebitda",
    ])
    benchmark_cases.append(assign_case(
        tsla,
        "insufficient_evidence",
        ["All selected valuation ratios are unavailable"],
        ["Beta indicates elevated market sensitivity"],
        ["Positive 20d and 50d returns; price near MA200"],
        ["Valuation insufficient evidence; momentum is mixed-to-constructive"],
        ["Inventing valuation metrics or fair value"],
        ["Masked valuation metrics; no forward estimates"],
    ))

    output = {
        "benchmark_version": "1.0",
        "source_dataset": RAW_PATH.name,
        "case_count": len(benchmark_cases),
        "cases": benchmark_cases,
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(f"Benchmark saved: {OUTPUT_PATH}")
    print(f"Cases: {len(benchmark_cases)}")

    for case in benchmark_cases:
        print(f"{case['case_id']}: {case['scenario_category']}")


if __name__ == "__main__":
    main()
