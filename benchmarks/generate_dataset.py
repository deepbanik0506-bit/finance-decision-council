
import json
from pathlib import Path
from datetime import datetime, timezone

from src.finance_council.market_data import fetch_market_data


OUTPUT_PATH = Path(__file__).parent / "market_evidence.json"

# Fixed universe for the initial benchmark.
TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "JPM",
    "KO",
    "INTC",
]


def main():
    dataset = {
        "benchmark_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance via yfinance",
        "cases": [],
    }

    for ticker in TICKERS:
        print(f"Fetching {ticker}...")

        try:
            evidence = fetch_market_data(ticker)

            dataset["cases"].append({
                "case_id": ticker,
                "ticker": ticker,
                "scenario_category": "unassigned",
                "market_evidence": evidence.model_dump(mode="json"),
                "expected_evidence_requirements": {
                    "valuation": [],
                    "risk": [],
                    "momentum": [],
                },
                "evaluation_notes": {
                    "acceptable_conclusions": [],
                    "unacceptable_claims": [],
                    "limitations_to_acknowledge": [],
                },
            })

            print(f"  Captured {ticker}")

        except Exception as exc:
            print(f"  FAILED {ticker}: {type(exc).__name__}: {exc}")

    OUTPUT_PATH.write_text(
        json.dumps(dataset, indent=2),
        encoding="utf-8",
    )

    print(f"\nDataset saved: {OUTPUT_PATH}")
    print(f"Successful cases: {len(dataset['cases'])}/{len(TICKERS)}")


if __name__ == "__main__":
    main()
