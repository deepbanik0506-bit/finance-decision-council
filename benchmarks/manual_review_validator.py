
"""Validation for structured manual-review benchmark files."""

from datetime import datetime


REQUIRED_TOP_LEVEL_FIELDS = {
    "case_id",
    "ticker",
    "review_timestamp",
    "agent_scores",
    "council_score",
    "critical_failures",
    "case_status",
}

AGENTS = ["valuation", "risk", "momentum"]

AGENT_DIMENSIONS = [
    "evidence_grounding",
    "unsupported_claims",
    "analytical_defensibility",
    "limitation_acknowledgment",
]

COUNCIL_DIMENSION = "outlook_consistency"

VALID_CRITICAL_FAILURES = {
    "CF-01",
    "CF-02",
    "CF-03",
    "CF-04",
    "CF-05",
}

VALID_CASE_STATUSES = {
    "PASS",
    "FAIL",
    "REVIEW REQUIRED",
}


def validate_manual_review(review: dict) -> list[str]:
    """Return validation errors. Empty list means valid."""
    errors = []

    # 1. Top-level structure
    if not isinstance(review, dict):
        return ["Review must be a JSON object."]

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in review:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # 2. Required metadata
    for field in ("case_id", "ticker"):
        value = review[field]

        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be non-empty text.")

    # 3. Review timestamp (ISO-8601)
    timestamp = review["review_timestamp"]

    if not isinstance(timestamp, str):
        errors.append("review_timestamp must be an ISO-8601 string.")
    else:
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            errors.append("review_timestamp must be valid ISO-8601.")

    # 4. Agent score structure and values
    agent_scores = review["agent_scores"]

    if not isinstance(agent_scores, dict):
        errors.append("agent_scores must be an object.")
    else:
        for agent in AGENTS:
            if agent not in agent_scores:
                errors.append(f"Missing agent_scores.{agent}")
                continue

            scores = agent_scores[agent]

            if not isinstance(scores, dict):
                errors.append(f"agent_scores.{agent} must be an object.")
                continue

            for dimension in AGENT_DIMENSIONS:
                if dimension not in scores:
                    errors.append(
                        f"Missing agent_scores.{agent}.{dimension}"
                    )
                    continue

                entry = scores[dimension]

                if not isinstance(entry, dict):
                    errors.append(
                        f"agent_scores.{agent}.{dimension} must be an object."
                    )
                    continue

                if "score" not in entry:
                    errors.append(
                        f"Missing score: {agent}.{dimension}"
                    )
                    continue

                if "justification" not in entry:
                    errors.append(
                        f"Missing justification: {agent}.{dimension}"
                    )
                    continue

                score = entry["score"]
                justification = entry["justification"]

                # Score must be integer 0-5 (bool is rejected)
                if (
                    not isinstance(score, int)
                    or isinstance(score, bool)
                    or not 0 <= score <= 5
                ):
                    errors.append(
                        f"Invalid score: {agent}.{dimension} "
                        "(must be integer 0-5)"
                    )

                # Justification must be non-empty text
                if (
                    not isinstance(justification, str)
                    or not justification.strip()
                ):
                    errors.append(
                        f"Invalid justification: {agent}.{dimension}"
                    )

                # Scores 1 and 4 require interpolation justification
                if (
                    isinstance(score, int)
                    and not isinstance(score, bool)
                    and score in (1, 4)
                    and isinstance(justification, str)
                ):
                    if "interpolat" not in justification.lower():
                        errors.append(
                            f"{agent}.{dimension}: score {score} "
                            "requires interpolation justification"
                        )

    # 5. Council score
    council_score = review["council_score"]

    if not isinstance(council_score, dict):
        errors.append("council_score must be an object.")
    else:
        entry = council_score.get(COUNCIL_DIMENSION)

        if entry is None:
            errors.append(
                "Missing council_score.outlook_consistency"
            )
        elif not isinstance(entry, dict):
            errors.append(
                "council_score.outlook_consistency must be an object."
            )
        else:
            score = entry.get("score")
            justification = entry.get("justification")

            if (
                not isinstance(score, int)
                or isinstance(score, bool)
                or not 0 <= score <= 5
            ):
                errors.append(
                    "Invalid council outlook_consistency score "
                    "(must be integer 0-5)"
                )

            if (
                not isinstance(justification, str)
                or not justification.strip()
            ):
                errors.append(
                    "Invalid council outlook_consistency justification"
                )

            if (
                isinstance(score, int)
                and not isinstance(score, bool)
                and score in (1, 4)
                and isinstance(justification, str)
            ):
                if "interpolat" not in justification.lower():
                    errors.append(
                        "Council scores 1 and 4 require "
                        "interpolation justification"
                    )

    # 6. Critical failure records
    critical_failures = review["critical_failures"]

    if not isinstance(critical_failures, list):
        errors.append("critical_failures must be a list.")
    else:
        failure_ids = set()

        for index, failure in enumerate(critical_failures):
            prefix = f"critical_failures[{index}]"

            if not isinstance(failure, dict):
                errors.append(f"{prefix} must be an object.")
                continue

            required_failure_fields = {
                "failure_id",
                "component",
                "category",
                "problematic_claim",
                "evidence_reference",
                "justification",
                "affected_dimension",
            }

            for field in required_failure_fields:
                if field not in failure:
                    errors.append(f"Missing {prefix}.{field}")

            failure_id = failure.get("failure_id")

            if not isinstance(failure_id, str) or not failure_id.strip():
                errors.append(f"{prefix}.failure_id must be non-empty.")
            elif failure_id in failure_ids:
                errors.append(f"Duplicate failure_id: {failure_id}")
            else:
                failure_ids.add(failure_id)

            category = failure.get("category")

            if (
    not isinstance(category, str)
    or category not in VALID_CRITICAL_FAILURES
            ):
                errors.append(
                    f"{prefix}.category must be one of "
                    f"{sorted(VALID_CRITICAL_FAILURES)}"
                )

            for field in (
                "component",
                "problematic_claim",
                "evidence_reference",
                "justification",
                "affected_dimension",
            ):
                value = failure.get(field)

                if not isinstance(value, str) or not value.strip():
                    errors.append(
                        f"{prefix}.{field} must be non-empty text."
                    )

    # 7. Case status consistency
    case_status = review["case_status"]

    if (
    not isinstance(case_status, str)
    or case_status not in VALID_CASE_STATUSES
    ):
        errors.append(
            f"case_status must be one of {sorted(VALID_CASE_STATUSES)}"
        )
    elif isinstance(critical_failures, list):
        if case_status == "PASS" and critical_failures:
            errors.append(
                "PASS cannot contain critical failures."
            )

        if case_status == "FAIL" and not critical_failures:
            errors.append(
                "FAIL requires at least one critical failure."
            )

    return errors
