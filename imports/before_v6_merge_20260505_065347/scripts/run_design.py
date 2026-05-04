#!/usr/bin/env python3
"""design-run skill — concept stage executor.

Pipeline:
  1. Load Project entity
  2. Load Prompt entity (default: prm_run_concept)
  3. Read ingest manifest; resolve consumed assets
  4. Build prompt context (incl. project_overrides)
  5. Render prompt → RenderedPrompt
  6. Execute LLM mode:
       - dry-run: produce a deterministic stub Plan (no LLM)
       - hook   : call out to a user-provided LLM hook script (stdin → stdout JSON)
       - live   : reserved for native API integration (P2)
  7. Validate Plan vs schema
  8. Write Plan note + JSON
  9. Write Run log; append run_id to project.run_history

Standard library only. No mutation of source assets, no Vault writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from shared import (  # noqa: E402
    frontmatter, manifest as manifest_mod, project_loader,
    prompt_loader, prompt_render, schema,
    rule_loader, pattern_loader, recommendation_engine,
)


SKILL_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_run_id(now: datetime) -> str:
    return f"run_run_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"


def _make_plan_id(project_id: str, stage: str, now: datetime) -> str:
    slug = project_id.removeprefix("prj_")
    return f"pln_{slug}_{stage}_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"


def _canonical_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Asset summarization (manifest record → prompt input shape)
# ---------------------------------------------------------------------------

def _summarize_asset(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "category": record.get("category"),
        "name": Path(record.get("source_path", "")).name,
        "family_role": record.get("family_role"),
        "confidence": record.get("confidence"),
    }


# A small lexicon of "signal-y" tokens we extract from project context.
# Keep this conservative — over-broad signals create false positive matches.
_BRIEF_SIGNAL_LEXICON = {
    # 中文 / 英文 — 设计行业常见概念信号
    "新品", "新品发布", "限定", "高端", "极简", "克制", "促销",
    "重塑", "改版", "首发", "联名", "节日", "周年",
    "premium", "minimal", "launch", "limited", "rebrand", "anniversary",
}


def _derive_brief_signals(project: project_loader.Project) -> list[str]:
    """Extract a list of brief-signal tokens from the project's brief_summary
    and open_questions. P1 implementation: lexicon match.

    Conservative: a token must be present as a substring of the brief or
    a deliverable name to be considered.
    """
    haystack_parts = [project.brief_summary or ""]
    for d in project.deliverables:
        haystack_parts.append(str(d.get("name", "")))
    for q in project.open_questions:
        haystack_parts.append(str(q))
    haystack = " ".join(haystack_parts).lower()

    signals: list[str] = []
    for token in _BRIEF_SIGNAL_LEXICON:
        if token.lower() in haystack:
            signals.append(token)
    return signals


def _resolve_consumed_assets(
    project: project_loader.Project,
    manifest: manifest_mod.Manifest,
    explicit: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Decide which assets this run consumes.

    Priority:
      1. --asset CLI args (explicit)
      2. project.asset_refs intersected with manifest
      3. all assets in manifest matching deliverable categories

    Returns (consumed_ids, warnings).
    """
    warnings: list[str] = []

    if explicit:
        consumed = []
        for aid in explicit:
            if manifest.get(aid) is None:
                warnings.append(f"--asset {aid!r} not found in manifest, skipping")
                continue
            consumed.append(aid)
        return consumed, warnings

    if project.asset_refs:
        consumed = [aid for aid in project.asset_refs if manifest.get(aid) is not None]
        missing = [aid for aid in project.asset_refs if manifest.get(aid) is None]
        for aid in missing:
            warnings.append(f"project.asset_refs has {aid!r} but manifest doesn't")
        if consumed:
            return consumed, warnings
        warnings.append("project.asset_refs gave no matches; falling back to deliverable category match")

    deliverable_cats = {d.get("category") for d in project.deliverables if d.get("category")}
    if not deliverable_cats:
        return [], warnings + ["no deliverable categories declared"]

    consumed = []
    for record in manifest.records:
        if record.get("category") in deliverable_cats:
            consumed.append(record["id"])
    return consumed, warnings


# ---------------------------------------------------------------------------
# LLM modes
# ---------------------------------------------------------------------------

def _execute_dry_run(rendered: prompt_render.RenderedPrompt,
                     project: project_loader.Project) -> dict[str, Any]:
    """Produce a deterministic stub LLM output. No API call.

    The stub structure is shaped to satisfy output_schema validation
    in P2; for now it provides 2 placeholder directions.
    """
    deliverables = rendered.declared_inputs.get("deliverables") or []
    asset_summaries = rendered.declared_inputs.get("asset_summaries") or []
    pattern_refs = rendered.declared_inputs.get("pattern_refs") or []

    primary_assets = [a["id"] for a in asset_summaries[:3]]
    primary_patterns = list(pattern_refs)[:1]

    directions = [
        {
            "id": "dir_001",
            "name": "克制冷感",
            "core_idea": f"以高端冷调主导的 {project.project_type} 路线，强调材质感与留白。",
            "visual_approach": "深色背景 + 单色高饱和强调色 + 极简几何排版。",
            "rationale": "服务 brief 中 '高端、避免促销感' 的核心要求。",
            "referenced_patterns": primary_patterns,
            "referenced_assets": primary_assets,
        },
        {
            "id": "dir_002",
            "name": "光影叙事",
            "core_idea": "用光影作为主要视觉语言，构建产品在场景中被发现的瞬间。",
            "visual_approach": "强对比光影 + 实拍质感 + 隐性产品出现。",
            "rationale": "差异化于第一向，提供 brief 之外的延展空间。",
            "referenced_patterns": [],
            "referenced_assets": primary_assets[:1],
        },
    ]

    next_actions = [
        f"基于 dir_001 完成 1 个主视觉 v1 草稿（覆盖 {len(deliverables)} 类交付）",
        "邀请客户对 dir_001 / dir_002 表态",
    ]
    open_questions = list(rendered.declared_inputs.get("open_questions") or [])
    if not open_questions:
        open_questions = ["客户对哪一向更倾向？是否需要再增加一向？"]

    return {
        "directions": directions,
        "next_actions": next_actions,
        "open_questions_for_client": open_questions,
        "_dry_run": True,
    }


def _execute_hook(rendered: prompt_render.RenderedPrompt, hook_path: Path) -> dict[str, Any]:
    """Invoke an external script that takes RenderedPrompt JSON on stdin
    and emits LLM JSON on stdout. This isolates the LLM call from this script.
    """
    payload = {
        "system": rendered.system,
        "user": rendered.user,
        "model_hint": rendered.model_hint,
        "temperature_hint": rendered.temperature_hint,
        "output_format": rendered.output_format,
        "output_schema": rendered.output_schema,
        "prompt_id": rendered.prompt_id,
        "prompt_version": rendered.prompt_version,
    }
    proc = subprocess.run(
        [str(hook_path)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"LLM hook failed (rc={proc.returncode}): {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM hook returned invalid JSON: {exc}\nstdout: {proc.stdout[:500]}") from exc


# ---------------------------------------------------------------------------
# Plan + Run record builders
# ---------------------------------------------------------------------------

def build_plan_fm(
    *,
    plan_id: str,
    project: project_loader.Project,
    stage: str,
    run_id: str,
    rendered: prompt_render.RenderedPrompt,
    llm_output: dict[str, Any],
    consumed_assets: list[str],
    consumed_patterns: list[str],
    llm_mode: str,
    now: str,
) -> dict[str, Any]:
    raw_directions = list(llm_output.get("directions") or [])
    directions = []
    for i, d in enumerate(raw_directions, start=1):
        if not isinstance(d, dict):
            continue
        # Ensure each direction has an id
        d_with_id = dict(d)
        d_with_id.setdefault("id", f"dir_{i:03d}")
        d_with_id.setdefault("referenced_patterns", [])
        d_with_id.setdefault("referenced_assets", [])
        directions.append(d_with_id)
    if not directions:
        directions.append({
            "id": "dir_001",
            "name": "fallback",
            "core_idea": "(LLM produced no directions)",
            "visual_approach": "",
            "rationale": "",
            "referenced_patterns": [],
            "referenced_assets": [],
        })

    return {
        "id": plan_id,
        "type": "plan",
        "schema_version": "1.0",
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "created_by": "skill:design-run",
        "source_run_id": run_id,
        "tags": ["design-run", stage],
        "project_id": project.id,
        "stage": stage,
        "prompt_id": rendered.prompt_id,
        "prompt_version": rendered.prompt_version,
        "prompt_inputs_hash": rendered.inputs_hash,
        "directions": directions,
        "next_actions": list(llm_output.get("next_actions") or []),
        "open_questions_for_client": list(llm_output.get("open_questions_for_client") or []),
        "consumed_assets": consumed_assets,
        "consumed_patterns": consumed_patterns,
        "llm_mode": llm_mode,
        "decision_notes": None,
        "adopted_direction_id": None,
        "superseded_by": None,
    }


def plan_note_body(fm: dict[str, Any], project: project_loader.Project) -> str:
    lines = [
        f"# Plan · {project.client} · {fm['stage']}",
        "",
        f"- Project: [[{project.id}]]",
        f"- Stage: {fm['stage']}",
        f"- Prompt: {fm['prompt_id']} v{fm['prompt_version']}",
        f"- LLM mode: {fm['llm_mode']}",
        f"- Status: {fm['status']}",
        "",
        "## Brief recap",
        project.brief_summary or "(无)",
        "",
        "## Directions",
        "",
    ]
    for d in fm["directions"]:
        lines.append(f"### {d['id']} · {d.get('name', '')}")
        lines.append(f"- Core idea: {d.get('core_idea', '')}")
        lines.append(f"- Visual approach: {d.get('visual_approach', '')}")
        lines.append(f"- Rationale: {d.get('rationale', '')}")
        if d.get("referenced_patterns"):
            lines.append(f"- Patterns: {', '.join(d['referenced_patterns'])}")
        if d.get("referenced_assets"):
            lines.append(f"- Assets: {', '.join(d['referenced_assets'])}")
        lines.append("")

    lines.append("## Next actions")
    for action in fm["next_actions"]:
        lines.append(f"- [ ] {action}")
    lines.append("")
    lines.append("## Open questions for client")
    for q in fm.get("open_questions_for_client") or []:
        lines.append(f"- {q}")
    return "\n".join(lines) + "\n"


def build_run_fm(
    *,
    run_id: str,
    started: datetime,
    finished: datetime,
    inputs: dict[str, Any],
    project_id: str,
    parent_run_id: str | None,
    rendered: prompt_render.RenderedPrompt,
    plan_id: str,
    plan_path: Path,
    consumed_assets: list[str],
    llm_mode: str,
    metrics: dict[str, Any],
    errors: list[dict[str, Any]],
    outcome: str,
) -> dict[str, Any]:
    started_iso = started.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    finished_iso = finished.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    duration_ms = int((finished - started).total_seconds() * 1000)
    return {
        "id": run_id,
        "type": "run",
        "schema_version": "1.0",
        "created_at": started_iso,
        "updated_at": finished_iso,
        "status": "active",
        "created_by": "skill:design-run",
        "source_run_id": None,
        "tags": ["run", "concept"],
        "skill": "design-run",
        "skill_version": SKILL_VERSION,
        "started_at": started_iso,
        "finished_at": finished_iso,
        "duration_ms": duration_ms,
        "outcome": outcome,
        "parent_run_id": parent_run_id,
        "project_id": project_id,
        "inputs": inputs,
        "inputs_hash": _canonical_hash(inputs),
        "rules_used": [],
        "prompts_used": [
            {
                "id": rendered.prompt_id,
                "version": rendered.prompt_version,
                "inputs_hash": rendered.inputs_hash,
                "llm_mode": llm_mode,
            }
        ],
        "outputs": [
            {"kind": "file", "path": str(plan_path), "role": "primary"},
            {"kind": "entity", "entity_id": plan_id, "action": "created"},
        ],
        "entities_created": [plan_id],
        "entities_updated": [],
        "metrics": metrics,
        "errors": errors,
        "decision": None,
        "next_eligible_skill": "design-critic",
    }


def run_note_body(fm: dict[str, Any]) -> str:
    m = fm["metrics"]
    return (
        f"# Run · design-run · {fm['started_at']}\n\n"
        f"- Project: {fm['project_id']}\n"
        f"- Parent run: {fm.get('parent_run_id') or '(none)'}\n"
        f"- Outcome: {fm['outcome']}\n"
        f"- Duration: {fm['duration_ms']} ms\n"
        f"- Plan: {fm['entities_created'][0]}\n"
        f"- Assets consumed: {m.get('consumed_assets_count', 0)}\n"
        f"- Directions produced: {m.get('directions_count', 0)}\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="design-run skill — concept stage executor.")
    parser.add_argument("--project", required=True, help="Path to project.md")
    parser.add_argument("--manifest", required=True, help="Path to manifest.jsonl from design-ingest")
    parser.add_argument("--prompts-dir", required=True, help="Directory of Prompt entities (50_Prompts/)")
    parser.add_argument("--out", required=True, help="Output directory for Plan and Run records")
    parser.add_argument("--patterns-dir",
                        help="Directory of Pattern entities (30_Patterns/). "
                             "If provided, design-run will run pattern recommendation.")
    parser.add_argument("--rules-dir",
                        help="Directory of Rule entities (40_Rules/). "
                             "Required if --patterns-dir is set, for the recommendation rule.")
    parser.add_argument("--recommendation-rule-id",
                        default="rul_recommend_pattern",
                        help="Rule id used for pattern recommendation (default: rul_recommend_pattern)")
    parser.add_argument("--top-k", type=int, default=3,
                        help="Max number of patterns to recommend (default: 3)")
    parser.add_argument("--pattern", action="append",
                        help="Force include specific Pattern id(s); skips recommendation for these")
    parser.add_argument("--no-recommend", action="store_true",
                        help="Disable pattern recommendation entirely")
    parser.add_argument("--no-update-pattern-counts", action="store_true",
                        help="Don't increment Pattern.reuse_count for recommended patterns")
    parser.add_argument("--prompt-id", default="prm_run_concept",
                        help="Prompt id to render (default: prm_run_concept)")
    parser.add_argument("--stage", default="concept",
                        choices=["kickoff", "concept", "iteration", "review", "final"])
    parser.add_argument("--asset", action="append", default=None,
                        help="Explicit Asset ID(s) to consume; repeatable")
    parser.add_argument("--llm", choices=["dry-run", "hook"], default="dry-run",
                        help="LLM mode (default: dry-run)")
    parser.add_argument("--llm-hook", help="Path to executable hook script (required if --llm hook)")
    parser.add_argument("--update-project", action="store_true",
                        help="Append run_id to project.run_history on success")
    parser.add_argument("--strict", action="store_true",
                        help="Abort on schema validation failure")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    run_id = _make_run_id(started)

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []

    # --- Load Project ---
    try:
        project = project_loader.load_project(Path(args.project).expanduser().resolve())
    except project_loader.ProjectLoadError as exc:
        print(f"ERROR: failed to load project: {exc}", file=sys.stderr)
        return 2

    # --- Load Manifest ---
    try:
        manifest = manifest_mod.load_manifest(Path(args.manifest).expanduser().resolve())
    except manifest_mod.ManifestReadError as exc:
        print(f"ERROR: failed to load manifest: {exc}", file=sys.stderr)
        return 2

    parent_run_id = manifest.source_run_id()
    if not parent_run_id:
        print("ERROR: manifest contains no source_run_id; cannot establish parent run.", file=sys.stderr)
        return 2

    # --- Load Prompt ---
    try:
        prompts = prompt_loader.load_prompts(Path(args.prompts_dir).expanduser().resolve())
    except prompt_loader.PromptLoadError as exc:
        print(f"ERROR: failed to load prompts: {exc}", file=sys.stderr)
        return 2
    if args.prompt_id not in prompts:
        print(f"ERROR: prompt {args.prompt_id!r} not found in {args.prompts_dir}", file=sys.stderr)
        return 2
    prompt = prompts[args.prompt_id]

    # --- Resolve consumed assets ---
    consumed_ids, warnings = _resolve_consumed_assets(project, manifest, args.asset)
    for w in warnings:
        errors.append({"level": "warning", "code": "asset_resolution", "target": "", "message": w})

    consumed_records = manifest.by_ids(consumed_ids)
    asset_summaries = [_summarize_asset(r) for r in consumed_records]

    # --- Pattern recommendation ---
    recommended_patterns: list[recommendation_engine.Recommendation] = []
    forced_pattern_ids: list[str] = list(args.pattern or [])
    consumed_patterns: list[str] = []
    pattern_recommendation_log: dict[str, Any] = {"mode": "disabled"}
    pattern_increments: dict[str, int] = {}

    if not args.no_recommend and args.patterns_dir:
        if not args.rules_dir:
            errors.append({"level": "warning", "code": "recommend_skipped",
                           "target": "", "message": "--patterns-dir set but --rules-dir not provided"})
            pattern_recommendation_log = {"mode": "skipped", "reason": "no rules_dir"}
        else:
            try:
                patterns = pattern_loader.load_patterns(
                    Path(args.patterns_dir).expanduser().resolve()
                )
            except pattern_loader.PatternLoadError as exc:
                errors.append({"level": "warning", "code": "pattern_load_failure",
                               "target": "", "message": str(exc)})
                patterns = {}

            try:
                rules = rule_loader.load_rules(Path(args.rules_dir).expanduser().resolve())
            except rule_loader.RuleLoadError as exc:
                errors.append({"level": "warning", "code": "rule_load_failure",
                               "target": "", "message": str(exc)})
                rules = {}

            rule = rules.get(args.recommendation_rule_id)
            if rule is None:
                errors.append({"level": "warning", "code": "recommendation_rule_missing",
                               "target": args.recommendation_rule_id,
                               "message": f"recommendation rule {args.recommendation_rule_id!r} not found"})
                pattern_recommendation_log = {"mode": "skipped", "reason": "rule missing"}
            elif not patterns:
                pattern_recommendation_log = {"mode": "executed", "candidates": 0,
                                              "recommendations": []}
            else:
                # Build ProjectContext
                deliverable_cats = list({d.get("category") for d in project.deliverables
                                         if d.get("category")})
                # Extract brief signals (P1: simple — use deliverable names + open_questions tokens)
                brief_signals = _derive_brief_signals(project)

                ctx = recommendation_engine.ProjectContext(
                    project_id=project.id,
                    project_type=project.project_type,
                    deliverable_categories=deliverable_cats,
                    brief_signals=brief_signals,
                    stage=args.stage,
                    client_traits=[],
                )

                try:
                    recommended_patterns = recommendation_engine.recommend_patterns(
                        rule, list(patterns.values()), ctx,
                    )
                except recommendation_engine.RecommendationError as exc:
                    errors.append({"level": "warning", "code": "recommendation_failure",
                                   "target": "", "message": str(exc)})
                    recommended_patterns = []

                # Apply top-k cap
                top_recs = recommended_patterns[:args.top_k]
                consumed_patterns = [r.pattern_id for r in top_recs]
                pattern_recommendation_log = {
                    "mode": "executed",
                    "candidates": len(patterns),
                    "rule_id": rule.id,
                    "rule_version": rule.version,
                    "recommendations": [
                        {
                            "pattern_id": r.pattern_id,
                            "title": r.title,
                            "weighted_score": r.weighted_score,
                            "dimension_scores": r.dimension_scores,
                        }
                        for r in top_recs
                    ],
                }

                # Update reuse_count for actually consumed patterns
                if not args.no_update_pattern_counts:
                    for rec in top_recs:
                        if rec.pattern_id not in patterns:
                            continue
                        try:
                            new_count = pattern_loader.increment_reuse_count(
                                patterns[rec.pattern_id].source_path
                            )
                            pattern_increments[rec.pattern_id] = new_count
                        except Exception as exc:
                            errors.append({"level": "warning",
                                           "code": "pattern_count_update_failure",
                                           "target": rec.pattern_id, "message": str(exc)})

    # Merge forced patterns (not from recommender) at the front
    if forced_pattern_ids:
        for pid in reversed(forced_pattern_ids):  # preserve user order, push to front
            if pid not in consumed_patterns:
                consumed_patterns.insert(0, pid)
        pattern_recommendation_log["forced"] = forced_pattern_ids

    # --- Build prompt context (apply project.prompt_overrides) ---
    overrides = project.prompt_overrides.get(prompt.id, {})
    # Pattern refs in prompt = forced + recommended + project's own pattern_refs (legacy)
    # consumed_patterns is already forced-first; merge with project.pattern_refs for completeness
    prompt_pattern_refs: list[str] = list(consumed_patterns)
    for pid in project.pattern_refs:
        if pid not in prompt_pattern_refs:
            prompt_pattern_refs.append(pid)

    context: dict[str, Any] = {
        "project_id": project.id,
        "brief_summary": project.brief_summary,
        "client": project.client,
        "project_type": project.project_type,
        "deliverables": project.deliverables,
        "asset_summaries": asset_summaries,
        "pattern_refs": prompt_pattern_refs,
        "open_questions": project.open_questions,
        "tone_override": overrides.get("tone_override", ""),
        "must_avoid": overrides.get("must_avoid", []),
    }

    # --- Render ---
    try:
        rendered = prompt_render.render(prompt, context)
    except prompt_render.RenderError as exc:
        print(f"ERROR: prompt render failed: {exc}", file=sys.stderr)
        return 3

    # --- Execute LLM ---
    if args.llm == "dry-run":
        llm_output = _execute_dry_run(rendered, project)
        llm_mode = "dry-run"
    elif args.llm == "hook":
        if not args.llm_hook:
            print("ERROR: --llm hook requires --llm-hook PATH", file=sys.stderr)
            return 2
        try:
            llm_output = _execute_hook(rendered, Path(args.llm_hook).expanduser().resolve())
            llm_mode = "hook"
        except Exception as exc:
            errors.append({"level": "error", "code": "llm_hook_failure", "target": "", "message": str(exc)})
            print(f"ERROR: {exc}", file=sys.stderr)
            llm_output = {"directions": [], "next_actions": [], "open_questions_for_client": []}
            llm_mode = "hook"
    else:
        print(f"ERROR: unsupported llm mode {args.llm!r}", file=sys.stderr)
        return 2

    # --- Build Plan ---
    now_str = _now_iso()
    plan_id = _make_plan_id(project.id, args.stage, started)
    plan_fm = build_plan_fm(
        plan_id=plan_id,
        project=project,
        stage=args.stage,
        run_id=run_id,
        rendered=rendered,
        llm_output=llm_output,
        consumed_assets=consumed_ids,
        consumed_patterns=consumed_patterns,
        llm_mode=llm_mode,
        now=now_str,
    )

    # --- Validate Plan ---
    try:
        schema.validate(plan_fm, "plan")
    except schema.SchemaError as exc:
        errors.append({"level": "error" if args.strict else "warning",
                       "code": "plan_schema_invalid", "target": plan_id, "message": str(exc)})
        if args.strict:
            print(f"ERROR: plan schema invalid: {exc}", file=sys.stderr)
            return 4

    # --- Write Plan ---
    plan_path = out_dir / f"{plan_id}.md"
    frontmatter.write(plan_path, plan_fm, plan_note_body(plan_fm, project))

    plan_jsonl_path = out_dir / f"{plan_id}.jsonl"
    plan_jsonl_path.write_text(json.dumps(plan_fm, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- Write rendered prompt snapshot (for debugging / replay) ---
    snapshot_path = out_dir / f"{plan_id}.prompt.txt"
    snapshot_path.write_text(
        f"# Prompt snapshot — {rendered.prompt_id} v{rendered.prompt_version}\n"
        f"# inputs_hash: {rendered.inputs_hash}\n\n"
        f"--- SYSTEM ---\n{rendered.system or '(none)'}\n\n"
        f"--- USER ---\n{rendered.user}\n",
        encoding="utf-8",
    )

    # --- Build Run record ---
    finished = datetime.now(timezone.utc)
    metrics = {
        "consumed_assets_count": len(consumed_ids),
        "directions_count": len(plan_fm["directions"]),
        "asset_summaries_in_prompt": len(asset_summaries),
        "patterns_recommended": len(consumed_patterns),
        "pattern_recommendation": pattern_recommendation_log,
        "pattern_reuse_count_increments": pattern_increments,
        "elapsed_perf_seconds": round(time.perf_counter() - started_perf, 4),
    }

    inputs = {
        "project_path": str(Path(args.project).expanduser().resolve()),
        "manifest_path": str(Path(args.manifest).expanduser().resolve()),
        "prompts_dir": str(Path(args.prompts_dir).expanduser().resolve()),
        "out_path": str(out_dir),
        "prompt_id": args.prompt_id,
        "stage": args.stage,
        "explicit_assets": args.asset,
        "llm_mode": args.llm,
    }

    has_error = any(e.get("level") == "error" for e in errors)
    outcome = "failure" if has_error else ("partial" if errors else "success")

    run_fm = build_run_fm(
        run_id=run_id,
        started=started,
        finished=finished,
        inputs=inputs,
        project_id=project.id,
        parent_run_id=parent_run_id,
        rendered=rendered,
        plan_id=plan_id,
        plan_path=plan_path,
        consumed_assets=consumed_ids,
        llm_mode=llm_mode,
        metrics=metrics,
        errors=errors,
        outcome=outcome,
    )

    try:
        schema.validate(run_fm, "run")
    except schema.SchemaError as exc:
        print(f"WARNING: run record failed schema validation: {exc}", file=sys.stderr)

    run_path = out_dir / f"{run_id}.md"
    frontmatter.write(run_path, run_fm, run_note_body(run_fm))

    # --- Update project (opt-in) ---
    if args.update_project and outcome == "success":
        try:
            project_loader.append_run_to_history(Path(args.project).expanduser().resolve(), run_id)
        except Exception as exc:
            print(f"WARNING: failed to update project run_history: {exc}", file=sys.stderr)

    # --- Summary ---
    print(f"Project:        {project.id}")
    print(f"Stage:          {args.stage}")
    print(f"Parent run:     {parent_run_id}")
    print(f"Run id:         {run_id}")
    print(f"Plan id:        {plan_id}")
    print(f"Assets used:    {len(consumed_ids)}")
    print(f"Patterns used:  {len(consumed_patterns)} {consumed_patterns or '(none)'}")
    if recommended_patterns:
        print(f"  recommended:")
        for r in recommended_patterns[:args.top_k]:
            forced_marker = ""
            print(f"    - {r.pattern_id} (score={r.weighted_score}) - {r.title}")
    print(f"Directions:     {len(plan_fm['directions'])}")
    print(f"LLM mode:       {llm_mode}")
    print(f"Outcome:        {outcome}")
    print(f"  plan:    {plan_path}")
    print(f"  prompt:  {snapshot_path}")
    print(f"  run:     {run_path}")
    if errors:
        print(f"  warnings/errors: {len(errors)}")

    return 0 if outcome != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
