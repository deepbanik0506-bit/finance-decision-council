
"""Tests for structured manual-review validation."""

from benchmarks.manual_review_validator import validate_manual_review


def valid_review():
    """Return a structurally valid manual-review record."""
    review = {
        "case_id": "AAPL",
        "ticker": "AAPL",
        "review_timestamp": "2026-11-05T12:00:00Z",
        "agent_scores": {},
        "council_score": {
            "outlook_consistency": {
                "score": 3,
                "justification": "The outlook is consistent with agent findings.",
            }
        },
        "critical_failures": [],
        "case_status": "PASS",
    }

    dimensions = [
        "evidence_grounding",
        "unsupported_claims",
        "analytical_defensibility",
        "limitation_acknowledgment",
    ]

    for agent in ["valuation", "risk", "momentum"]:
        review["agent_scores"][agent] = {}

        for dimension in dimensions:
            review["agent_scores"][agent][dimension] = {
                "score": 3,
                "justification": "The analysis is adequately supported.",
            }

    return review


def test_valid_review_passes():
    review = valid_review()

    assert validate_manual_review(review) == []


def test_missing_top_level_field_rejected():
    review = valid_review()
    del review["ticker"]

    errors = validate_manual_review(review)

    assert any("ticker" in error for error in errors)


def test_score_outside_range_rejected():
    review = valid_review()
    review["agent_scores"]["valuation"]["evidence_grounding"]["score"] = 6

    errors = validate_manual_review(review)

    assert any("Invalid score" in error for error in errors)


def test_boolean_score_rejected():
    review = valid_review()
    review["agent_scores"]["risk"]["unsupported_claims"]["score"] = True

    errors = validate_manual_review(review)

    assert any("Invalid score" in error for error in errors)


def test_empty_justification_rejected():
    review = valid_review()
    review["agent_scores"]["momentum"]["analytical_defensibility"][
        "justification"
    ] = "   "

    errors = validate_manual_review(review)

    assert any("Invalid justification" in error for error in errors)


def test_interpolation_score_requires_explanation():
    review = valid_review()
    review["agent_scores"]["valuation"]["evidence_grounding"] = {
        "score": 4,
        "justification": "Strong evidence supports this score.",
    }

    errors = validate_manual_review(review)

    assert any("interpolation" in error.lower() for error in errors)


def test_interpolation_score_with_explanation_passes():
    review = valid_review()
    review["agent_scores"]["valuation"]["evidence_grounding"] = {
        "score": 4,
        "justification": "Interpolated between anchors 3 and 5.",
    }

    errors = validate_manual_review(review)

    assert not any("interpolation" in error.lower() for error in errors)


def test_invalid_timestamp_rejected():
    review = valid_review()
    review["review_timestamp"] = "not-a-date"

    errors = validate_manual_review(review)

    assert any("ISO-8601" in error for error in errors)


def test_pass_with_critical_failure_rejected():
    review = valid_review()
    review["critical_failures"] = [
        {
            "failure_id": "CF-001",
            "component": "valuation",
            "category": "CF-01",
            "problematic_claim": "Fabricated revenue figure.",
            "evidence_reference": "market_evidence.json",
            "justification": "Claim is absent from frozen evidence.",
            "affected_dimension": "evidence_grounding",
        }
    ]

    errors = validate_manual_review(review)

    assert any("PASS cannot contain" in error for error in errors)


def test_fail_without_critical_failure_rejected():
    review = valid_review()
    review["case_status"] = "FAIL"

    errors = validate_manual_review(review)

    assert any("FAIL requires" in error for error in errors)


def test_duplicate_failure_ids_rejected():
    review = valid_review()

    failure = {
        "failure_id": "CF-001",
        "component": "valuation",
        "category": "CF-01",
        "problematic_claim": "Fabricated revenue figure.",
        "evidence_reference": "market_evidence.json",
        "justification": "Claim is absent from frozen evidence.",
        "affected_dimension": "evidence_grounding",
    }

    review["critical_failures"] = [failure, failure.copy()]
    review["case_status"] = "FAIL"

    errors = validate_manual_review(review)

    assert any("Duplicate failure_id" in error for error in errors)


def test_agent_scores_wrong_type_rejected():
    review = valid_review()
    review["agent_scores"] = []

    errors = validate_manual_review(review)

    assert any("agent_scores must be an object" in error for error in errors)


def test_agent_nested_scores_wrong_type_rejected():
    review = valid_review()
    review["agent_scores"]["valuation"] = []

    errors = validate_manual_review(review)

    assert any("valuation must be an object" in error for error in errors)


def test_council_score_wrong_type_rejected():
    review = valid_review()
    review["council_score"] = []

    errors = validate_manual_review(review)

    assert any("council_score must be an object" in error for error in errors)


def test_critical_failures_wrong_type_rejected():
    review = valid_review()
    review["critical_failures"] = {}

    errors = validate_manual_review(review)

    assert any("critical_failures must be a list" in error for error in errors)


def test_critical_failure_non_object_rejected():
    review = valid_review()
    review["critical_failures"] = ["invalid failure"]

    errors = validate_manual_review(review)

    assert any("must be an object" in error for error in errors)


def test_unhashable_case_status_does_not_crash():
    review = valid_review()
    review["case_status"] = []

    try:
        errors = validate_manual_review(review)
    except Exception as exc:
        assert False, f"Validator crashed: {exc}"

    assert errors


def test_unhashable_critical_failure_category_does_not_crash():
    review = valid_review()
    review["critical_failures"] = [
        {
            "failure_id": "CF-001",
            "component": "valuation",
            "category": [],
            "problematic_claim": "Claim",
            "evidence_reference": "evidence.json",
            "justification": "Reason",
            "affected_dimension": "evidence_grounding",
        }
    ]
    review["case_status"] = "FAIL"

    try:
        errors = validate_manual_review(review)
    except Exception as exc:
        assert False, f"Validator crashed: {exc}"

    assert errors
