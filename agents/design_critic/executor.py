"""Rule-based Design Critic executor.

This is the first real local agent executor for the file-driven runtime. It
does not call an LLM or external API; it scores known issue flags from the run
record and writes a structured critique report.
"""

from __future__ import annotations

from typing import Any


ISSUE_RULES: dict[str, dict[str, str | int]] = {
    "text_overlap": {
        "label": "Text overlap",
        "penalty": 3,
        "recommendation": "Separate overlapping text blocks, increase spacing, and re-export before review.",
    },
    "font_too_small": {
        "label": "Font too small",
        "penalty": 2,
        "recommendation": "Increase title and body font sizes for phone-screen readability.",
    },
    "visual_overload": {
        "label": "Visual overload",
        "penalty": 2,
        "recommendation": "Reduce content density and keep one primary message per design.",
    },
    "style_mismatch": {
        "label": "Style mismatch",
        "penalty": 2,
        "recommendation": "Realign color, typography, and visual tone with the brand brief.",
    },
}

APPROVAL_THRESHOLD = 8


def execute_design_critic(run: dict[str, Any]) -> dict[str, Any]:
    inputs = run.get("inputs") if isinstance(run.get("inputs"), dict) else {}
    flags = inputs.get("critique_flags") if isinstance(inputs, dict) else {}
    if not isinstance(flags, dict):
        flags = {}

    issues: dict[str, dict[str, Any]] = {}
    total_penalty = 0
    recommendations: list[str] = []

    for key, rule in ISSUE_RULES.items():
        failed = bool(flags.get(key, False))
        penalty = int(rule["penalty"]) if failed else 0
        total_penalty += penalty
        if failed:
            recommendations.append(str(rule["recommendation"]))
        issues[key] = {
            "label": rule["label"],
            "failed": failed,
            "penalty": penalty,
            "recommendation": rule["recommendation"] if failed else "No action needed.",
        }

    score = max(0, 10 - total_penalty)
    approved = score >= APPROVAL_THRESHOLD and not any(issue["failed"] for issue in issues.values())
    recommendation = "approve" if approved else "retry"

    outputs = run.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        outputs = {"notes": str(outputs)}
        run["outputs"] = outputs

    outputs["review_report"] = {
        "agent": "design_critic",
        "mode": "rule_based_mock_critique",
        "score": score,
        "approved": approved,
        "recommendation": recommendation,
        "issues": issues,
        "summary": _summary(issues, approved),
        "revision_actions": recommendations,
    }
    run["review_score"] = score
    run["approved"] = approved
    run["recommendation"] = recommendation
    run["next_action"] = (
        "Route to publisher for archive or release."
        if approved
        else "Retry: " + " ".join(recommendations)
    )
    return run


def _summary(issues: dict[str, dict[str, Any]], approved: bool) -> str:
    if approved:
        return "Design passed the local rule-based critique."
    failed = [key for key, issue in issues.items() if issue["failed"]]
    return "Design failed local critique: " + ", ".join(failed) + "."
