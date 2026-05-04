"""Schema validator for Design Data Factory entities.

Implements the constraints from references/schemas/. Only validates the
entities that scan_inbox actually writes (asset, run); other entities can
be added in P1.

Keep this minimal — it's a guardrail, not a full JSON Schema validator.
"""

from __future__ import annotations

import re
from typing import Any


class SchemaError(ValueError):
    """Raised when a frontmatter dict fails schema validation."""


# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------

ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

VALID_STATUS = {"draft", "staged", "active", "archived", "deprecated"}


def _require(fm: dict[str, Any], field: str, entity: str) -> Any:
    if field not in fm or fm[field] in (None, ""):
        raise SchemaError(f"{entity}: missing required field '{field}'")
    return fm[field]


def _check_common(fm: dict[str, Any], entity: str, expected_type: str) -> None:
    for f in ("id", "type", "schema_version", "created_at", "updated_at",
              "status", "created_by"):
        _require(fm, f, entity)
    if fm["type"] != expected_type:
        raise SchemaError(f"{entity}: type must be '{expected_type}', got {fm['type']!r}")
    if fm["status"] not in VALID_STATUS:
        raise SchemaError(f"{entity}: status {fm['status']!r} not in {sorted(VALID_STATUS)}")
    for f in ("created_at", "updated_at"):
        v = fm[f]
        if not isinstance(v, str) or not ISO8601_RE.match(v):
            raise SchemaError(f"{entity}: {f} must be ISO8601 UTC, got {v!r}")


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------

VALID_CATEGORIES = {
    "poster", "space", "soft-decoration", "brand",
    "proposal", "process", "reference", "unknown",
}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_FAMILY_ROLES = {"original", "variant", "final", "derivative"}

_ASSET_ID_RE = re.compile(r"^ast_[a-f0-9]{12}$")


def validate_asset(fm: dict[str, Any]) -> None:
    _check_common(fm, "asset", "asset")
    asset_id = fm["id"]
    if not _ASSET_ID_RE.match(asset_id):
        raise SchemaError(f"asset: id {asset_id!r} must match pattern ast_<sha256[:12]>")

    for f in ("source_run_id", "category", "confidence", "needs_review",
              "evidence", "source_path", "source_hash", "source_size_bytes",
              "source_modified", "extension"):
        if f not in fm:
            raise SchemaError(f"asset: missing required field {f!r}")

    if fm["category"] not in VALID_CATEGORIES:
        raise SchemaError(f"asset: category {fm['category']!r} invalid")
    if fm["confidence"] not in VALID_CONFIDENCE:
        raise SchemaError(f"asset: confidence {fm['confidence']!r} invalid")
    if not isinstance(fm["needs_review"], bool):
        raise SchemaError("asset: needs_review must be bool")
    if not isinstance(fm["evidence"], list):
        raise SchemaError("asset: evidence must be list")

    sha = fm["source_hash"]
    if not isinstance(sha, str) or not SHA256_RE.match(sha):
        raise SchemaError(f"asset: source_hash must be sha256 hex, got {sha!r}")
    if asset_id[4:] != sha[:12]:
        raise SchemaError(f"asset: id suffix {asset_id[4:]!r} must equal source_hash[:12] {sha[:12]!r}")

    ext = fm["extension"]
    if not isinstance(ext, str) or (ext and not ext.startswith(".")):
        raise SchemaError(f"asset: extension must start with '.', got {ext!r}")

    fr = fm.get("family_role")
    if fr is not None and fr not in VALID_FAMILY_ROLES:
        raise SchemaError(f"asset: family_role {fr!r} invalid")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

VALID_SKILLS = {"design-ingest", "design-run", "design-critic", "design-archive"}
VALID_OUTCOMES = {"success", "partial", "failure"}

_RUN_ID_RE = re.compile(r"^run_[a-z_]+_\d{8}_\d{6}_[a-z0-9]{4}$")


def validate_run(fm: dict[str, Any]) -> None:
    _check_common(fm, "run", "run")
    run_id = fm["id"]
    if not _RUN_ID_RE.match(run_id):
        raise SchemaError(f"run: id {run_id!r} does not match pattern")
    if fm["status"] not in {"active", "deprecated"}:
        raise SchemaError(f"run: status must be active or deprecated, got {fm['status']!r}")

    for f in ("skill", "skill_version", "started_at", "finished_at",
              "duration_ms", "outcome", "inputs", "inputs_hash", "outputs"):
        if f not in fm:
            raise SchemaError(f"run: missing required field {f!r}")

    if fm["skill"] not in VALID_SKILLS:
        raise SchemaError(f"run: skill {fm['skill']!r} invalid")
    if fm["outcome"] not in VALID_OUTCOMES:
        raise SchemaError(f"run: outcome {fm['outcome']!r} invalid")
    if not isinstance(fm["duration_ms"], int) or fm["duration_ms"] < 0:
        raise SchemaError("run: duration_ms must be non-negative int")
    if not isinstance(fm["inputs"], dict):
        raise SchemaError("run: inputs must be dict")
    if not isinstance(fm["outputs"], list):
        raise SchemaError("run: outputs must be list")
    ih = fm["inputs_hash"]
    if not isinstance(ih, str) or not SHA256_RE.match(ih):
        raise SchemaError(f"run: inputs_hash must be sha256 hex, got {ih!r}")

    if fm["outcome"] == "failure":
        errors = fm.get("errors", [])
        has_error = any(isinstance(e, dict) and e.get("level") == "error" for e in errors)
        if not has_error:
            raise SchemaError("run: outcome=failure requires at least one error-level entry in errors")


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

VALID_STAGES = {"kickoff", "concept", "iteration", "review", "final"}
VALID_PLAN_STATUSES = {"draft", "reviewed", "adopted", "superseded", "deprecated"}
VALID_LLM_MODES = {"dry-run", "hook", "live"}

_PLAN_ID_RE = re.compile(r"^pln_[a-z0-9_]+_\d{8}_\d{6}_[a-f0-9]{4}$")


def validate_plan(fm: dict[str, Any]) -> None:
    # Plan has its own status enum (includes "reviewed", "adopted", "superseded"
    # which are plan-specific). Bypass _check_common's status check.
    for f in ("id", "type", "schema_version", "created_at", "updated_at",
              "status", "created_by"):
        _require(fm, f, "plan")
    if fm["type"] != "plan":
        raise SchemaError(f"plan: type must be 'plan', got {fm['type']!r}")
    if fm["status"] not in VALID_PLAN_STATUSES:
        raise SchemaError(f"plan: status {fm['status']!r} invalid (allowed: {sorted(VALID_PLAN_STATUSES)})")
    for f in ("created_at", "updated_at"):
        v = fm[f]
        if not isinstance(v, str) or not ISO8601_RE.match(v):
            raise SchemaError(f"plan: {f} must be ISO8601 UTC, got {v!r}")

    pid = fm["id"]
    if not _PLAN_ID_RE.match(pid):
        raise SchemaError(f"plan: id {pid!r} does not match pattern")

    for f in ("project_id", "stage", "prompt_id", "prompt_version",
              "prompt_inputs_hash", "directions", "next_actions",
              "consumed_assets", "llm_mode"):
        if f not in fm:
            raise SchemaError(f"plan: missing required field {f!r}")

    if fm["stage"] not in VALID_STAGES:
        raise SchemaError(f"plan: stage {fm['stage']!r} invalid")
    if fm["llm_mode"] not in VALID_LLM_MODES:
        raise SchemaError(f"plan: llm_mode {fm['llm_mode']!r} invalid")
    if not isinstance(fm["directions"], list) or len(fm["directions"]) < 1:
        raise SchemaError("plan: directions must be non-empty list")

    seen_ids: set[str] = set()
    for d in fm["directions"]:
        if not isinstance(d, dict):
            raise SchemaError("plan: each direction must be a dict")
        for required in ("id", "name", "core_idea", "visual_approach", "rationale"):
            if required not in d:
                raise SchemaError(f"plan: direction missing field {required!r}")
        did = d["id"]
        if did in seen_ids:
            raise SchemaError(f"plan: duplicate direction id {did!r}")
        seen_ids.add(did)

    ih = fm["prompt_inputs_hash"]
    if not isinstance(ih, str) or not SHA256_RE.match(ih):
        raise SchemaError(f"plan: prompt_inputs_hash must be sha256 hex, got {ih!r}")

    if fm["status"] == "adopted":
        ad_id = fm.get("adopted_direction_id")
        if not ad_id or ad_id not in seen_ids:
            raise SchemaError("plan: status=adopted requires adopted_direction_id in directions")


# ---------------------------------------------------------------------------
# Critique
# ---------------------------------------------------------------------------

VALID_TARGET_TYPES = {"plan_direction", "plan", "asset"}
VALID_DECISIONS = {"pass", "revise", "fail"}
VALID_CRITIQUE_STATUSES = {"active", "deprecated"}

_CRITIQUE_ID_RE = re.compile(r"^crt_[a-z0-9_]+_\d{8}_\d{6}_[a-f0-9]{4}$")


def validate_critique(fm: dict[str, Any]) -> None:
    # Critique uses a restricted status enum like Run
    for f in ("id", "type", "schema_version", "created_at", "updated_at",
              "status", "created_by"):
        _require(fm, f, "critique")
    if fm["type"] != "critique":
        raise SchemaError(f"critique: type must be 'critique', got {fm['type']!r}")
    if fm["status"] not in VALID_CRITIQUE_STATUSES:
        raise SchemaError(f"critique: status {fm['status']!r} invalid")
    for f in ("created_at", "updated_at"):
        v = fm[f]
        if not isinstance(v, str) or not ISO8601_RE.match(v):
            raise SchemaError(f"critique: {f} must be ISO8601 UTC, got {v!r}")

    cid = fm["id"]
    if not _CRITIQUE_ID_RE.match(cid):
        raise SchemaError(f"critique: id {cid!r} does not match pattern")

    for f in ("source_run_id", "target_type", "target_plan_id", "project_id",
              "rubric_id", "rubric_version", "scores", "weighted_score",
              "decision", "decision_rationale", "llm_mode"):
        if f not in fm:
            raise SchemaError(f"critique: missing required field {f!r}")

    if fm["target_type"] not in VALID_TARGET_TYPES:
        raise SchemaError(f"critique: target_type {fm['target_type']!r} invalid")
    if fm["target_type"] == "plan_direction" and not fm.get("target_direction_id"):
        raise SchemaError("critique: target_type=plan_direction requires target_direction_id")
    if fm["decision"] not in VALID_DECISIONS:
        raise SchemaError(f"critique: decision {fm['decision']!r} invalid")
    if fm["llm_mode"] not in VALID_LLM_MODES:
        raise SchemaError(f"critique: llm_mode {fm['llm_mode']!r} invalid")

    rationale = fm["decision_rationale"]
    if not isinstance(rationale, str) or len(rationale) > 500:
        raise SchemaError("critique: decision_rationale must be string ≤500 chars")

    scores = fm["scores"]
    if not isinstance(scores, list) or len(scores) < 1:
        raise SchemaError("critique: scores must be non-empty list")
    seen_dims: set[str] = set()
    weight_sum = 0.0
    weighted_actual = 0.0
    for s in scores:
        if not isinstance(s, dict):
            raise SchemaError("critique: each score must be a dict")
        for required in ("dimension_id", "score", "weight"):
            if required not in s:
                raise SchemaError(f"critique: score missing field {required!r}")
        did = s["dimension_id"]
        if did in seen_dims:
            raise SchemaError(f"critique: duplicate dimension_id {did!r}")
        seen_dims.add(did)
        if not isinstance(s["score"], int):
            raise SchemaError(f"critique: score for {did!r} must be int, got {type(s['score']).__name__}")
        weight_sum += float(s["weight"])
        weighted_actual += s["score"] * float(s["weight"])

    if abs(weight_sum - 1.0) > 0.01:
        raise SchemaError(f"critique: scores weights sum to {weight_sum}, not ~1.0")

    declared = float(fm["weighted_score"])
    if abs(declared - weighted_actual) > 0.01:
        raise SchemaError(
            f"critique: weighted_score {declared} != computed {round(weighted_actual, 4)}"
        )

    if fm.get("prompt_id"):
        for required in ("prompt_version", "prompt_inputs_hash"):
            if not fm.get(required):
                raise SchemaError(f"critique: prompt_id present but {required!r} missing")
        ih = fm["prompt_inputs_hash"]
        if not isinstance(ih, str) or not SHA256_RE.match(ih):
            raise SchemaError(f"critique: prompt_inputs_hash must be sha256 hex, got {ih!r}")


# ---------------------------------------------------------------------------
# Pattern
# ---------------------------------------------------------------------------

VALID_PATTERN_STATUSES = {"draft", "active", "archived", "deprecated"}
VALID_ASPECTS = {"composition", "color", "typography", "material", "motion", "cultural"}

_PATTERN_ID_RE = re.compile(r"^pat_[a-z0-9_]+$")


def validate_pattern(fm: dict[str, Any]) -> None:
    for f in ("id", "type", "schema_version", "created_at", "updated_at",
              "status", "created_by"):
        _require(fm, f, "pattern")
    if fm["type"] != "pattern":
        raise SchemaError(f"pattern: type must be 'pattern', got {fm['type']!r}")
    if fm["status"] not in VALID_PATTERN_STATUSES:
        raise SchemaError(f"pattern: status {fm['status']!r} invalid")
    for f in ("created_at", "updated_at"):
        v = fm[f]
        if not isinstance(v, str) or not ISO8601_RE.match(v):
            raise SchemaError(f"pattern: {f} must be ISO8601, got {v!r}")

    pid = fm["id"]
    if not _PATTERN_ID_RE.match(pid):
        raise SchemaError(f"pattern: id {pid!r} does not match pattern")

    for f in ("source_run_id", "pattern_version", "category", "title", "summary",
              "applicable_when", "core_elements", "evidence_assets",
              "derived_from_projects", "derived_from_runs",
              "derived_from_critique_id", "reuse_score", "reuse_count"):
        if f not in fm:
            raise SchemaError(f"pattern: missing required field {f!r}")

    if fm["category"] not in VALID_CATEGORIES:
        raise SchemaError(f"pattern: category {fm['category']!r} invalid")
    if not isinstance(fm["title"], str) or not fm["title"]:
        raise SchemaError("pattern: title must be non-empty string")
    if len(fm["title"]) > 30:
        raise SchemaError(f"pattern: title length {len(fm['title'])} > 30")
    if not isinstance(fm["summary"], str) or len(fm["summary"]) > 200:
        raise SchemaError("pattern: summary must be string ≤ 200 chars")

    evidence = fm["evidence_assets"]
    if not isinstance(evidence, list) or len(evidence) < 2:
        raise SchemaError("pattern: evidence_assets must have ≥ 2 entries")
    if not isinstance(fm["derived_from_projects"], list) or len(fm["derived_from_projects"]) < 1:
        raise SchemaError("pattern: derived_from_projects must have ≥ 1 entry")
    if not isinstance(fm["derived_from_runs"], list) or len(fm["derived_from_runs"]) < 1:
        raise SchemaError("pattern: derived_from_runs must have ≥ 1 entry")

    elements = fm["core_elements"]
    if not isinstance(elements, list) or len(elements) < 1:
        raise SchemaError("pattern: core_elements must be non-empty list")
    has_must_have = False
    for e in elements:
        if not isinstance(e, dict):
            raise SchemaError("pattern: each core_element must be a dict")
        for required in ("aspect", "description", "must_have"):
            if required not in e:
                raise SchemaError(f"pattern: core_element missing field {required!r}")
        if e["aspect"] not in VALID_ASPECTS:
            raise SchemaError(f"pattern: invalid aspect {e['aspect']!r}")
        if e.get("must_have") is True:
            has_must_have = True
    if not has_must_have:
        raise SchemaError("pattern: at least one core_element must have must_have=true")

    rs = fm["reuse_score"]
    if not isinstance(rs, (int, float)) or rs < 0 or rs > 1:
        raise SchemaError(f"pattern: reuse_score {rs!r} not in [0, 1]")
    rc = fm["reuse_count"]
    if not isinstance(rc, int) or rc < 0:
        raise SchemaError(f"pattern: reuse_count {rc!r} must be non-negative int")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

VALIDATORS = {
    "asset": validate_asset,
    "run": validate_run,
    "plan": validate_plan,
    "critique": validate_critique,
    "pattern": validate_pattern,
}


def validate(fm: dict[str, Any], entity_type: str) -> None:
    """Validate frontmatter dict for the given entity type.

    Raises SchemaError on any violation. Returns None on success.
    """
    if entity_type not in VALIDATORS:
        raise SchemaError(f"unknown entity_type {entity_type!r}; supported: {sorted(VALIDATORS)}")
    VALIDATORS[entity_type](fm)
