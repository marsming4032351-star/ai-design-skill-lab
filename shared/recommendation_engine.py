"""Pattern recommendation engine.

Given a project context and a set of Pattern entities, score each pattern
against a recommendation rubric (engine: weighted, domain: recommendation)
and return a ranked Top-K.

Decoupled from any LLM. Pure data computation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .pattern_loader import Pattern
from .rule_loader import Rule


class RecommendationError(ValueError):
    pass


@dataclass
class ProjectContext:
    """The 'query' side of recommendation."""
    project_id: str
    project_type: str
    deliverable_categories: list[str]
    brief_signals: list[str]
    stage: str
    client_traits: list[str] = field(default_factory=list)


@dataclass
class Recommendation:
    pattern_id: str
    title: str
    weighted_score: float
    dimension_scores: dict[str, int]
    reasons: list[str]


# ---------------------------------------------------------------------------
# Per-dimension scoring functions
# ---------------------------------------------------------------------------

def _score_applicability(pattern: Pattern, ctx: ProjectContext) -> tuple[int, list[str]]:
    """4-component applicability check, returns 1-5 score."""
    aw = pattern.fm.get("applicable_when") or {}
    components = 0
    matched: list[str] = []

    # 1. project_type match
    if ctx.project_type in (aw.get("project_types") or []):
        components += 1
        matched.append(f"project_type={ctx.project_type}")

    # 2. category overlap
    cat_overlap = set(ctx.deliverable_categories) & set(aw.get("categories") or [])
    if cat_overlap:
        components += 1
        matched.append(f"categories={','.join(sorted(cat_overlap))}")

    # 3. brief_signals match ratio
    p_signals = set(aw.get("brief_signals") or [])
    proj_signals = set(ctx.brief_signals or [])
    if p_signals and proj_signals:
        # Substring match — pattern signals can be substrings of project signals
        hit = sum(1 for ps in p_signals if any(ps in pj or pj in ps for pj in proj_signals))
        ratio = hit / max(len(p_signals), 1)
        if ratio >= 0.5:
            components += 1
            matched.append(f"brief_signals_match={hit}/{len(p_signals)}")
        elif ratio > 0:
            components += 0.5
            matched.append(f"brief_signals_partial={hit}/{len(p_signals)}")
    elif not p_signals:
        # Pattern has no signal constraint → neutral, count as matched
        components += 0.5

    # 4. stage match
    if ctx.stage in (aw.get("stages") or []):
        components += 1
        matched.append(f"stage={ctx.stage}")

    # Map components (0..4) to 1..5
    score = round(1 + (components / 4.0) * 4)
    return max(1, min(5, score)), matched


def _score_quality(pattern: Pattern) -> tuple[int, str]:
    rs = float(pattern.fm.get("reuse_score", 0))
    if rs >= 0.9:
        return 5, f"reuse_score={rs:.2f}"
    if rs >= 0.7:
        return 4, f"reuse_score={rs:.2f}"
    if rs >= 0.4:
        return 3, f"reuse_score={rs:.2f}"
    if rs >= 0.2:
        return 2, f"reuse_score={rs:.2f}"
    return 1, f"reuse_score={rs:.2f}"


def _score_validation(pattern: Pattern) -> tuple[int, str]:
    rc = int(pattern.fm.get("reuse_count", 0))
    capped = min(rc, 5)
    score = max(1, capped if capped >= 1 else 1)
    if rc == 0:
        return 1, "reuse_count=0 (never used)"
    if rc <= 2:
        return 3, f"reuse_count={rc}"
    return 5, f"reuse_count={rc} (well-validated)"


def _score_recency(pattern: Pattern, now: datetime) -> tuple[int, str]:
    created = pattern.fm.get("created_at", "")
    try:
        # Parse ISO8601, expecting Z suffix
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 1, f"unparseable created_at={created!r}"
    days_old = (now - dt).days
    if days_old < 90:
        return 5, f"{days_old}d old"
    if days_old < 180:
        return 4, f"{days_old}d old"
    if days_old < 365:
        return 3, f"{days_old}d old"
    if days_old < 730:
        return 2, f"{days_old}d old"
    return 1, f"{days_old}d old"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def recommend_patterns(
    rule: Rule,
    patterns: list[Pattern],
    ctx: ProjectContext,
    now: datetime | None = None,
) -> list[Recommendation]:
    """Score and rank patterns. Returns sorted list (highest first), filtered
    by status and threshold per the rule's body.
    """
    if rule.engine != "weighted":
        raise RecommendationError(f"rule {rule.id!r} engine is {rule.engine!r}, expected weighted")
    if rule.fm.get("domain") != "recommendation":
        raise RecommendationError(f"rule {rule.id!r} domain is not 'recommendation'")

    body = rule.body
    dims = body.get("dimensions") or []
    weights: dict[str, float] = {}
    for d in dims:
        weights[d["id"]] = float(d.get("weight", 0))
    if abs(sum(weights.values()) - 1.0) > 0.01:
        raise RecommendationError(
            f"rule {rule.id!r} dimension weights sum to {sum(weights.values())}, not 1.0"
        )

    threshold = float(body.get("recommendation_threshold", 3.0))
    min_score = float(body.get("min_score", 1.0))
    status_filter = body.get("status_filter") or {}
    accept_statuses = set(status_filter.get("accept") or ["active"])

    if now is None:
        now = datetime.now(timezone.utc)

    recommendations: list[Recommendation] = []
    for pat in patterns:
        if pat.status not in accept_statuses:
            continue

        # Compute per-dimension scores
        applicability, app_reasons = _score_applicability(pat, ctx)
        quality, q_reason = _score_quality(pat)
        validation, v_reason = _score_validation(pat)
        recency, r_reason = _score_recency(pat, now)

        scores = {
            "applicability": applicability,
            "quality": quality,
            "validation": validation,
            "recency": recency,
        }

        # Weighted total
        weighted = sum(scores[d_id] * weights[d_id] for d_id in scores if d_id in weights)
        weighted = round(weighted, 4)

        if weighted < min_score:
            continue

        reasons: list[str] = [
            f"applicability={applicability} ({'; '.join(app_reasons) or 'no overlap'})",
            f"quality={quality} ({q_reason})",
            f"validation={validation} ({v_reason})",
            f"recency={recency} ({r_reason})",
        ]

        recommendations.append(Recommendation(
            pattern_id=pat.id,
            title=pat.title,
            weighted_score=weighted,
            dimension_scores=scores,
            reasons=reasons,
        ))

    # Sort high → low
    recommendations.sort(key=lambda r: r.weighted_score, reverse=True)

    # Filter by threshold
    above_threshold = [r for r in recommendations if r.weighted_score >= threshold]
    return above_threshold
