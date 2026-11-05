import sys

from src.finance_council.market_data import fetch_market_data
from src.finance_council.council_graph import build_council_graph


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m src.finance_council TICKER")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    try:
        evidence = fetch_market_data(ticker)

        initial_state = {
            "evidence": evidence,
            "valuation": None,
            "risk": None,
            "momentum": None,
            "disagreement": None,
            "confidence": None,
            "final_outlook": None,
        }

        result = build_council_graph().invoke(initial_state)

        print("\n" + "=" * 60)
        print(f"FINANCE DECISION COUNCIL | {ticker}")
        print("=" * 60)

        print("\n[VALUATION]")
        print(result["valuation"].model_dump_json(indent=2))

        print("\n[RISK]")
        print(result["risk"].model_dump_json(indent=2))

        print("\n[MOMENTUM]")
        print(result["momentum"].model_dump_json(indent=2))

        print("\n[DISAGREEMENT]")
        print(result["disagreement"])

        print("\n[CONFIDENCE]")
        print(result["confidence"])

        print("\n[FINAL OUTLOOK]")
        print(result["final_outlook"])

        print("\n" + "=" * 60)

    except Exception as exc:
        print(f"Council execution failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
