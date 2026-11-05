# Finance Decision Council — Evaluation Rubric

## Purpose

Evaluate whether Council assessments are grounded in supplied market evidence, logically defensible, appropriately limited, and consistent with the evidence available.

This rubric does not evaluate future stock-price prediction accuracy or investment returns.

## Scoring Scale

| Score | Definition                                                                            |
| ----- | ------------------------------------------------------------------------------------- |
| 0     | Severe failure; fabricated or materially contradictory analysis                       |
| 1     | Major deficiencies; unsupported conclusions dominate                                  |
| 2     | Weak; partial evidence use with important reasoning gaps                              |
| 3     | Acceptable; broadly evidence-grounded with some deficiencies                          |
| 4     | Strong; evidence-grounded, logically defensible, limitations mostly acknowledged      |
| 5     | Excellent; precise, fully grounded, appropriately cautious, and internally consistent |

## Dimension-Specific Scoring Anchors

Scores of 0, 2, 3, and 5 use the behavioral anchors below. Scores of 1 and 4 represent intermediate performance between adjacent anchors and require reviewer justification.

### 1. Evidence Grounding

| Score | Anchor                                                                                                                                  |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Analysis relies on fabricated, unverifiable, or materially misrepresented evidence.                                                     |
| 2     | Multiple claims lack traceable evidence; evidence is selectively or inaccurately represented.                                           |
| 3     | Main claims are supported by available evidence; minor traceability or interpretation issues remain.                                    |
| 5     | Claims are precisely traceable to evidence; metrics are accurately represented; observations and interpretations are clearly separated. |

### 2. Unsupported Claims

| Score | Anchor                                                                                                               |
| ----- | -------------------------------------------------------------------------------------------------------------------- |
| 0     | Material unsupported claims or fabricated facts drive the analysis or recommendation.                                |
| 2     | Several unsupported assumptions, forecasts, peer comparisons, or certainty claims materially weaken the analysis.    |
| 3     | No material unsupported claims; minor assumptions are identifiable and do not distort conclusions.                   |
| 5     | Claims remain strictly within evidence boundaries; assumptions are explicit; uncertainty is appropriately expressed. |

### 3. Analytical Defensibility

| Score | Anchor                                                                                                                     |
| ----- | -------------------------------------------------------------------------------------------------------------------------- |
| 0     | Reasoning is fundamentally invalid, contradictory, or disconnected from evidence.                                          |
| 2     | Significant logical gaps, misleading interpretations, or unresolved contradictions weaken conclusions.                     |
| 3     | Reasoning is coherent and evidence-linked; conclusions are generally defensible with minor weaknesses.                     |
| 5     | Reasoning is rigorous, internally consistent, appropriately qualified, and defensible against alternative interpretations. |

### 4. Limitation Acknowledgment

| Score | Anchor                                                                                                                                                 |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0     | Material data limitations are ignored or missing evidence is treated as negative evidence.                                                             |
| 2     | Important limitations are omitted or inadequately incorporated into conclusions.                                                                       |
| 3     | Relevant limitations are acknowledged; conclusions are reasonably qualified.                                                                           |
| 5     | Limitations, missing data, methodological constraints, and historical-versus-forward-looking boundaries are explicitly integrated into interpretation. |

### 5. Outlook Consistency — Council Synthesis Only

| Score | Anchor                                                                                                                                                          |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Final outlook materially contradicts agent findings or asserts direction despite insufficient evidence.                                                         |
| 2     | Outlook inadequately represents disagreement, insufficient evidence, or material dimension limitations.                                                         |
| 3     | Outlook generally reflects agent findings, evidence sufficiency, and major conflicts; minor inconsistencies remain.                                             |
| 5     | Outlook accurately integrates valuation, risk, and momentum; preserves disagreement and insufficient evidence; and communicates direction only where justified. |

### Intermediate Scores

- **1:** Performance is between the 0 and 2 anchors.
- **4:** Performance is between the 3 and 5 anchors.
- Every intermediate score requires a written justification identifying why the response falls between the adjacent anchors.

## Evaluation Dimensions

### 1. Evidence Grounding

- Are claims traceable to supplied market evidence?
- Are metrics represented accurately?
- Are observations distinguished from interpretations?
- Are external facts or benchmarks introduced without evidence?

### 2. Unsupported Claims

- Does the agent invent financial metrics, peer comparisons, forecasts, or business facts?
- Does it claim certainty unsupported by the data?
- Does it treat missing evidence as negative evidence?

### 3. Analytical Defensibility

- Does the conclusion follow logically from available evidence?
- Are important contradictions acknowledged?
- Are assumptions reasonable and explicit?
- Does the agent avoid overstating what ratios or indicators establish?

### 4. Limitation Acknowledgment

- Are relevant data gaps identified?
- Does the agent acknowledge missing benchmarks, financial statements, or contextual evidence where relevant?
- Does it distinguish historical observations from forecasts?

### 5. Outlook Consistency

- Does the final outlook respect the valuation and momentum assessments?
- Are conflicts represented accurately?
- Does insufficient evidence prevent unsupported directional conclusions?
- Does risk analysis remain contextual rather than being misused as a directional signal?

## Scoring Allocation

- Valuation Agent: Evidence Grounding, Unsupported Claims,
  Analytical Defensibility, Limitation Acknowledgment.
- Risk Agent: Evidence Grounding, Unsupported Claims,
  Analytical Defensibility, Limitation Acknowledgment.
- Momentum Agent: Evidence Grounding, Unsupported Claims,
  Analytical Defensibility, Limitation Acknowledgment.
- Council Synthesis: Outlook Consistency only.

Total: 13 numerical scores per benchmark case.

## Review Procedure

For every benchmark case:

1. Inspect the frozen evidence.
2. Inspect each agent's structured output.
3. Inspect disagreement, evidence quality, analytical agreement, execution reliability, and final outlook.
4. Score each applicable dimension from 0–5.
5. Record a short justification for every score.
6. Record any critical failure separately.

### Quality Report Interpretation

- **Evidence Quality:** Assess whether each dimension has usable evidence, insufficient evidence, or failed execution.
- **Analytical Agreement:** Assess alignment or conflict between directional assessments. Non-directional risk analysis does not count as directional agreement.
- **Execution Reliability:** Assess whether agents executed successfully. Successful execution does not imply evidence sufficiency or analytical correctness.
- **Final Outlook:** Confirm that the synthesis preserves usable dimensions without overstating conclusions when other dimensions are insufficient or failed.
- Do not use an uncalibrated numeric confidence score as a substitute for these reports.

## Critical Failures

## Critical Failure Taxonomy

Critical failures are recorded independently from numerical dimension scores. A critical failure does not automatically force every dimension score to zero.

### CF-01: Evidence Fabrication

**Trigger:** An agent invents a metric, financial fact, or evidence and presents it as supplied market data.

**Examples:**

- Fabricated revenue, margins, or valuation ratios.
- Invented historical prices.
- Fictitious evidence attributed to the supplied dataset.

### CF-02: Unsupported Direction

**Trigger:** An agent asserts a directional conclusion despite insufficient evidence to support that conclusion.

**Examples:**

- Positive or negative valuation conclusion when valuation evidence is insufficient.
- Directional momentum conclusion unsupported by available indicators.

### CF-03: Evidence Misinterpretation

**Trigger:** Missing evidence is treated as negative evidence, or supplied evidence is materially misrepresented.

**Examples:**

- Missing financial data interpreted as poor financial performance.
- Incorrect interpretation of supplied market metrics materially affecting conclusions.

### CF-04: Synthesis Contradiction

**Trigger:** Council synthesis materially contradicts agent assessments without acknowledging or explaining the contradiction.

**Examples:**

- Final outlook contradicts directional agent findings without justification.
- Final synthesis disregards insufficient evidence reported by an agent.

### CF-05: Forecast Misrepresentation

**Trigger:** Historical market movement or technical indicators are represented as guaranteed future outcomes.

**Examples:**

- Historical price movement presented as a guaranteed forecast.
- An indicator treated as proof of future price direction.

### Critical Failure Recording Rules

For every critical failure:

1. Assign a unique failure ID within the benchmark case.
2. Record the responsible component: Valuation, Risk, Momentum, or Council Synthesis.
3. Record the critical failure category.
4. Record the exact problematic claim or output.
5. Identify the relevant frozen evidence or missing evidence.
6. Explain why the claim constitutes a critical failure.
7. Record the affected evaluation dimension.
8. Record the failure independently of numerical scores.

### Scoring Implications

- Critical failures do not automatically invalidate all dimension scores.
- Score each applicable dimension according to its own behavioral anchors.
- A critical failure may justify a score of 0 in the directly affected dimension when its anchor criteria are satisfied.
- Unaffected dimensions retain their independent scores.
- Critical failures must never be concealed by averaging numerical scores.
- A case containing critical failures must be explicitly flagged in the evaluation report.

### Case-Level Status

- **PASS:** No critical failures identified.
- **FAIL:** One or more critical failures identified.
- **REVIEW REQUIRED:** Reviewer cannot determine whether a suspected critical failure is substantiated.

Case-level status does not replace numerical scoring.

## Structured Manual-Review Schema

Every manually reviewed benchmark case must follow this structure.

### Required Fields

- `case_id`: Unique benchmark case identifier.
- `ticker`: Evaluated security.
- `review_timestamp`: Review completion timestamp.
- `agent_scores`: Numerical scores and justifications for Valuation, Risk, and Momentum.
- `council_score`: Numerical Outlook Consistency score and justification.
- `critical_failures`: Independently recorded critical failures.
- `case_status`: PASS, FAIL, or REVIEW REQUIRED.

### JSON Template

```json
{
  "case_id": "AAPL_001",
  "ticker": "AAPL",
  "review_timestamp": "ISO-8601 timestamp of actual review"
  "agent_scores": {
    "valuation": {
      "evidence_grounding": {
        "score": 3,
        "justification": "Main claims supported by supplied evidence."
      },
      "unsupported_claims": {
        "score": 3,
        "justification": "No material unsupported claims identified."
      },
      "analytical_defensibility": {
        "score": 3,
        "justification": "Reasoning generally follows supplied evidence."
      },
      "limitation_acknowledgment": {
        "score": 3,
        "justification": "Relevant limitations acknowledged."
      }
    },
    "risk": {
      "evidence_grounding": {
        "score": 3,
        "justification": "Risk assessment grounded in supplied evidence."
      },
      "unsupported_claims": {
        "score": 3,
        "justification": "No material unsupported claims identified."
      },
      "analytical_defensibility": {
        "score": 3,
        "justification": "Risk interpretation is defensible."
      },
      "limitation_acknowledgment": {
        "score": 3,
        "justification": "Relevant risk limitations acknowledged."
      }
    },
    "momentum": {
      "evidence_grounding": {
        "score": 3,
        "justification": "Momentum interpretation grounded in supplied indicators."
      },
      "unsupported_claims": {
        "score": 3,
        "justification": "No material unsupported claims identified."
      },
      "analytical_defensibility": {
        "score": 3,
        "justification": "Momentum interpretation follows available indicators."
      },
      "limitation_acknowledgment": {
        "score": 3,
        "justification": "Historical nature of indicators acknowledged."
      }
    }
  },
  "council_score": {
    "outlook_consistency": {
      "score": 3,
      "justification": "Final outlook generally reflects agent assessments."
    }
  },
  "critical_failures": [],
  "case_status": "PASS"
}
```

### Critical Failure Record Example

{
"failure_id": "CF-AAPL-001",
"component": "valuation",
"category": "CF-01",
"problematic_claim": "Example fabricated metric",
"evidence_reference": "frozen_evidence.json",
"justification": "Claim cannot be verified against supplied evidence.",
"affected_dimension": "evidence_grounding"
}

### Schema Rules

- Exactly 13 numerical scores per case.
- Scores of 1 or 4 must explicitly explain interpolation between adjacent anchors.
- Every score must be an integer from 0 to 5.
- Every score must include a non-empty justification.
- Intermediate scores 1 and 4 require explicit interpolation justification.
- Critical failures must use the defined CF-01 through CF-05 categories.
- Critical failure records must include component, category, problematic claim, evidence reference, justification, and affected dimension.
- `case_status` must follow the Critical Failure Taxonomy.
- Numerical averages must not determine case status.
