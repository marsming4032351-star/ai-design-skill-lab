"""Rubric scoring engine.

Applies a `engine: weighted` Rule to a set of dimension scores, producing
weighted_score and decision per the rubric's decision_rule.

Decoupled from LLM — design-critic feeds raw scores in, gets weighted_score
and decision out. Whether scores came from a human, an LLM, or a stub is
this engine's blind spot, by design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .rule_loader import Rule


class RubricError(ValueError):
    pass


@dataclass
class DimensionScore:
    dimension_id: str
    label: str
    score: int
    weight: float
    rationale: str = ""


@dataclass
class RubricResult:
    scores: list[DimensionScore]
    weighted_score: float
    decision: str  # pass | revise | fail
    decision_rationale: str
    rubric_id: str
    rubric_version: str


def apply_rubric(rubric: Rule, raw_scores: dict[str, dict[str, Any]]) -> RubricResult:
    """Apply a weighted-engine rubric to raw scores.

    raw_scores shape:
        {dimension_id: {score: int, rationale: str}}

    Validates:
      - all dimensions in rubric must be scored (or default to lowest)
      - all scores must be int within rubric.scale
      - dimension weights sum to ~1.0
    """
    if rubric.engine != "weighted":
        raise RubricError(f"rubric {rubric.id!r} has engine {rubric.engine!r}, expected weighted")

    body = rubric.body
    scale = body.get("scale") or [1, 5]
    scale_min, scale_max = int(scale[0]), int(scale[1])
    dimensions = body.get("dimensions") or []
    if not dimensions:
        raise RubricError(f"rubric {rubric.id!r} has no dimensions")

    # Validate weights sum
    weight_sum = sum(float(d.get("weight", 0)) for d in dimensions)
    if abs(weight_sum - 1.0) > 0.01:
        raise RubricError(f"rubric {rubric.id!r} dimension weights sum to {weight_sum}, not 1.0")

    # Compute per-dimension scores
    dim_scores: list[DimensionScore] = []
    missing: list[str] = []
    invalid: list[str] = []
    weighted_total = 0.0
    has_one = False

    for dim in dimensions:
        did = dim["id"]
        weight = float(dim["weight"])
        label = dim.get("label", did)

        raw = raw_scores.get(did)
        if raw is None:
            missing.append(did)
            continue
        score_val = raw.get("score")
        if not isinstance(score_val, int) or score_val < scale_min or score_val > scale_max:
            invalid.append(f"{did}={score_val!r}")
            continue
        if score_val == 1:
            has_one = True
        weighted_total += score_val * weight
        dim_scores.append(DimensionScore(
            dimension_id=did,
            label=label,
            score=score_val,
            weight=weight,
            rationale=str(raw.get("rationale", ""))[:200],
        ))

    if missing:
        raise RubricError(f"missing scores for dimensions: {missing}")
    if invalid:
        raise RubricError(f"invalid scores: {invalid}")

    weighted_score = round(weighted_total, 4)

    # Apply decision rule
    pass_threshold = float(body.get("pass_threshold", 3.5))
    fail_threshold = float(body.get("fail_threshold", 2.5))

    decision: str
    rationale_parts: list[str] = []

    if has_one:
        decision = "fail"
        rationale_parts.append("一项维度评分为 1（致命缺陷）")
    elif weighted_score < fail_threshold:
        decision = "fail"
        rationale_parts.append(f"weighted_score {weighted_score:.2f} < fail_threshold {fail_threshold}")
    elif weighted_score >= pass_threshold:
        # Also require all dims >= 2 (this is the rubric's "pass" condition)
        all_ge_2 = all(s.score >= 2 for s in dim_scores)
        if all_ge_2:
            decision = "pass"
            rationale_parts.append(
                f"weighted_score {weighted_score:.2f} >= pass_threshold {pass_threshold}；无维度 < 2"
            )
        else:
            decision = "revise"
            low_dims = [s.dimension_id for s in dim_scores if s.score < 2]
            rationale_parts.append(
                f"weighted_score {weighted_score:.2f} 达标，但维度 {low_dims} < 2，需修订"
            )
    else:
        decision = "revise"
        rationale_parts.append(
            f"weighted_score {weighted_score:.2f} 介于 [{fail_threshold}, {pass_threshold}) 之间"
        )

    return RubricResult(
        scores=dim_scores,
        weighted_score=weighted_score,
        decision=decision,
        decision_rationale="；".join(rationale_parts),
        rubric_id=rubric.id,
        rubric_version=rubric.version,
    )
