#!/usr/bin/env python3
"""design-archive skill — promote a passed direction into a reusable Pattern.

Pipeline:
  1. Load Critique (must have decision=pass)
  2. Load Plan; resolve target direction
  3. Load Project (must match)
  4. Load existing Patterns (for related_patterns + dedup)
  5. Resolve evidence assets from manifest (Plan.consumed_assets)
  6. Render extraction prompt → call LLM (dry-run / hook)
  7. Build Pattern frontmatter (incl. reuse_score from critique)
  8. Validate Pattern schema
  9. Write Pattern note + JSONL
 10. Update Plan (status, adopted_direction_id, decision_notes)
 11. Update Project (derived_pattern_refs)
 12. Update Asset notes (pattern_refs)
 13. Write Run log

Standard library only. No mutation of source assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
    frontmatter, manifest as manifest_mod,
    plan_loader, project_loader, critique_loader, pattern_loader,
    prompt_loader, prompt_render,
    schema, entity_updater,
)


SKILL_VERSION = "0.1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_run_id(now: datetime) -> str:
    return f"run_archive_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"


def _make_pattern_id(slug: str, project_id: str) -> str:
    """Build pat_<slug>; if slug clashes with project, prefix with project hint."""
    slug = re.sub(r"[^a-z0-9_]+", "_", slug.lower()).strip("_") or "pattern"
    return f"pat_{slug}"[:120]


def _canonical_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Asset summarization
# ---------------------------------------------------------------------------

def _summarize_evidence(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in records:
        out.append({
            "id": r["id"],
            "category": r.get("category"),
            "name": Path(r.get("source_path", "")).name,
            "family_role": r.get("family_role"),
        })
    return out


# ---------------------------------------------------------------------------
# LLM modes
# ---------------------------------------------------------------------------

def _execute_dry_run(rendered: prompt_render.RenderedPrompt,
                     direction: dict[str, Any],
                     project_type: str) -> dict[str, Any]:
    """Deterministic stub: produce a generic Pattern skeleton.

    Real LLM is required to produce a quality Pattern. dry-run gets the
    plumbing right and is useful for testing — the result is intentionally
    plain and clearly marked.
    """
    name = direction.get("name", "untitled")
    core_idea = direction.get("core_idea", "")
    return {
        "title": f"{name}（dry-run）"[:30],
        "summary": (core_idea[:180] + "（dry-run 抽取）")[:200],
        "slug": re.sub(r"[^a-z0-9_]+", "_", name.lower())[:24] + "_dryrun",
        "applicable_when": {
            "project_types": [project_type],
            "categories": [],
            "client_traits": [],
            "brief_signals": [],
            "stages": ["concept"],
        },
        "not_applicable_when": ["dry-run 抽取，未识别反例"],
        "core_elements": [
            {
                "aspect": "composition",
                "description": "（dry-run 占位）核心构图骨架",
                "must_have": True,
                "parameters": {},
            }
        ],
        "related_patterns": [],
        "_dry_run": True,
    }


def _execute_hook(rendered: prompt_render.RenderedPrompt,
                  hook_path: Path) -> dict[str, Any]:
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
        text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"LLM hook failed (rc={proc.returncode}): {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM hook returned invalid JSON: {exc}") from exc


# ---------------------------------------------------------------------------
# Build Pattern
# ---------------------------------------------------------------------------

def build_pattern_fm(
    *,
    pattern_id: str,
    project: project_loader.Project,
    plan: plan_loader.Plan,
    direction: dict[str, Any],
    critique: critique_loader.Critique,
    llm_output: dict[str, Any],
    evidence_asset_ids: list[str],
    archive_run_id: str,
    now: str,
    derived_runs: list[str],
) -> dict[str, Any]:
    # Derive reuse_score from critique's reuse_potential dimension (P1 direct mapping)
    reuse_dim_score = critique.score_for("reuse_potential") or 3
    reuse_score = round(reuse_dim_score / 5.0, 2)

    # Normalize core_elements: ensure each has an id
    raw_elements = list(llm_output.get("core_elements") or [])
    elements: list[dict[str, Any]] = []
    for i, e in enumerate(raw_elements, start=1):
        if not isinstance(e, dict):
            continue
        e2 = dict(e)
        e2.setdefault("id", f"elem_{i:03d}")
        e2.setdefault("must_have", False)
        e2.setdefault("parameters", {})
        elements.append(e2)
    if not any(e.get("must_have") for e in elements) and elements:
        elements[0]["must_have"] = True  # ensure at least one must_have

    applicable = llm_output.get("applicable_when") or {}
    if not isinstance(applicable, dict):
        applicable = {}
    # Auto-fill category from direction if missing
    cats = list(applicable.get("categories") or [])
    if not cats:
        # Use any deliverable category
        cats = list({d.get("category") for d in project.deliverables if d.get("category")})
    applicable["categories"] = cats

    return {
        "id": pattern_id,
        "type": "pattern",
        "schema_version": "1.0",
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "created_by": "skill:design-archive",
        "source_run_id": archive_run_id,
        "tags": ["design-archive", project.project_type],
        "pattern_version": "1.0.0",
        "category": (cats[0] if cats else "unknown"),
        "title": str(llm_output.get("title", ""))[:30],
        "summary": str(llm_output.get("summary", ""))[:200],
        "applicable_when": applicable,
        "not_applicable_when": list(llm_output.get("not_applicable_when") or []),
        "core_elements": elements,
        "evidence_assets": evidence_asset_ids,
        "derived_from_projects": [project.id],
        "derived_from_runs": derived_runs,
        "derived_from_critique_id": critique.id,
        "reuse_score": reuse_score,
        "reuse_count": 0,
        "related_patterns": list(llm_output.get("related_patterns") or []),
        "replaces": None,
        "replaced_by": None,
        "usage_examples": [
            {
                "project_id": project.id,
                "asset_id": evidence_asset_ids[0] if evidence_asset_ids else "",
                "note": f"首次抽取自 critique {critique.id}",
            }
        ],
    }


def pattern_note_body(fm: dict[str, Any], direction: dict[str, Any]) -> str:
    lines = [
        f"# Pattern · {fm['title']}",
        "",
        f"- Category: {fm['category']}",
        f"- reuse_score: {fm['reuse_score']}",
        f"- Derived from: [[{fm['derived_from_projects'][0]}]] / [[{fm['derived_from_critique_id']}]]",
        "",
        "## Summary",
        fm["summary"],
        "",
        "## Applicable when",
    ]
    aw = fm["applicable_when"]
    for key in ("project_types", "categories", "client_traits", "brief_signals", "stages"):
        vals = aw.get(key) or []
        if vals:
            lines.append(f"- {key}: {', '.join(str(v) for v in vals)}")

    if fm.get("not_applicable_when"):
        lines += ["", "## Not applicable when"]
        for s in fm["not_applicable_when"]:
            lines.append(f"- {s}")

    lines += ["", "## Core elements", ""]
    for e in fm["core_elements"]:
        marker = "**[must-have]**" if e.get("must_have") else "[optional]"
        lines.append(f"### {e['id']} · {e['aspect']} {marker}")
        lines.append(e.get("description", ""))
        params = e.get("parameters") or {}
        if params:
            lines.append("Parameters:")
            for k, v in params.items():
                lines.append(f"- {k}: {v}")
        lines.append("")

    lines += ["## Evidence", ""]
    for aid in fm["evidence_assets"]:
        lines.append(f"- [[{aid}]]")

    lines += ["", "## Origin", ""]
    lines.append(f"Derived from direction `{direction.get('id')}` ({direction.get('name', '')}) of plan.")
    lines.append(f"Critique decision: pass (score: see [[{fm['derived_from_critique_id']}]])")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Run record
# ---------------------------------------------------------------------------

def build_run_fm(
    *,
    run_id: str,
    started: datetime,
    finished: datetime,
    inputs: dict[str, Any],
    project_id: str,
    parent_run_id: str | None,
    rendered: prompt_render.RenderedPrompt,
    pattern_id: str,
    pattern_path: Path,
    entities_updated: list[str],
    update_log: dict[str, Any],
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
        "created_by": "skill:design-archive",
        "source_run_id": None,
        "tags": ["archive"],
        "skill": "design-archive",
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
            {"kind": "file", "path": str(pattern_path), "role": "primary"},
            {"kind": "entity", "entity_id": pattern_id, "action": "created"},
        ] + [
            {"kind": "entity", "entity_id": eid, "action": "updated"}
            for eid in entities_updated
        ],
        "entities_created": [pattern_id],
        "entities_updated": entities_updated,
        "metrics": {**metrics, "update_log": update_log},
        "errors": errors,
        "decision": None,
        "next_eligible_skill": None,
    }


def run_note_body(fm: dict[str, Any]) -> str:
    m = fm["metrics"]
    return (
        f"# Run · design-archive · {fm['started_at']}\n\n"
        f"- Project: {fm['project_id']}\n"
        f"- Parent run: {fm.get('parent_run_id') or '(none)'}\n"
        f"- Outcome: {fm['outcome']}\n"
        f"- Duration: {fm['duration_ms']} ms\n"
        f"- Pattern created: {fm['entities_created'][0]}\n"
        f"- Entities updated: {len(fm['entities_updated'])}\n"
        f"- Evidence asset count: {m.get('evidence_asset_count', 0)}\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="design-archive skill — promote a passed direction into a Pattern."
    )
    parser.add_argument("--critique", required=True, help="Path to critique .md (must have decision=pass)")
    parser.add_argument("--plan", required=True, help="Path to plan .md")
    parser.add_argument("--project", required=True, help="Path to project .md")
    parser.add_argument("--manifest", required=True, help="Path to ingest manifest.jsonl")
    parser.add_argument("--asset-notes-dir", help="Directory containing per-asset .md notes (for back-ref updates)")
    parser.add_argument("--patterns-dir", required=True, help="Directory containing existing patterns + where new pattern lands")
    parser.add_argument("--prompts-dir", required=True)
    parser.add_argument("--prompt-id", default="prm_archive_pattern_extract")
    parser.add_argument("--out", required=True, help="Where to write Run log (Pattern itself goes to --patterns-dir)")
    parser.add_argument("--llm", choices=["dry-run", "hook"], default="dry-run")
    parser.add_argument("--llm-hook")
    parser.add_argument("--evidence", action="append",
                        help="Override evidence asset IDs (repeatable). Default: Plan.consumed_assets")
    parser.add_argument("--no-update-plan", action="store_true",
                        help="Skip Plan status update (default: status → adopted)")
    parser.add_argument("--no-update-project", action="store_true")
    parser.add_argument("--no-update-assets", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    run_id = _make_run_id(started)

    out_dir = Path(args.out).expanduser().resolve()
    patterns_dir = Path(args.patterns_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    patterns_dir.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    update_log: dict[str, Any] = {}

    # --- Load Critique ---
    critique_path = Path(args.critique).expanduser().resolve()
    try:
        critique = critique_loader.load_critique(critique_path)
    except critique_loader.CritiqueLoadError as exc:
        print(f"ERROR: failed to load critique: {exc}", file=sys.stderr)
        return 2
    if critique.decision != "pass":
        print(f"ERROR: critique decision is {critique.decision!r}, not 'pass'. "
              f"Archive only operates on passed critiques.", file=sys.stderr)
        return 2

    # --- Load Plan ---
    plan_path = Path(args.plan).expanduser().resolve()
    try:
        plan = plan_loader.load_plan(plan_path)
    except plan_loader.PlanLoadError as exc:
        print(f"ERROR: failed to load plan: {exc}", file=sys.stderr)
        return 2
    if plan.id != critique.target_plan_id:
        print(f"ERROR: plan {plan.id} does not match critique.target_plan_id {critique.target_plan_id}",
              file=sys.stderr)
        return 2

    direction_id = critique.target_direction_id
    direction = plan.get_direction(direction_id) if direction_id else None
    if not direction:
        print(f"ERROR: direction {direction_id!r} not in plan {plan.id}", file=sys.stderr)
        return 2

    parent_run_id = critique.source_run_id  # archive's parent is the critic run

    # --- Load Project ---
    project_path = Path(args.project).expanduser().resolve()
    try:
        project = project_loader.load_project(project_path)
    except project_loader.ProjectLoadError as exc:
        print(f"ERROR: failed to load project: {exc}", file=sys.stderr)
        return 2
    if project.id != plan.project_id:
        print(f"ERROR: project {project.id} != plan.project_id {plan.project_id}", file=sys.stderr)
        return 2

    # --- Load existing Patterns ---
    try:
        existing_patterns = pattern_loader.load_patterns(patterns_dir)
    except pattern_loader.PatternLoadError as exc:
        print(f"ERROR: failed to load existing patterns: {exc}", file=sys.stderr)
        return 2

    # --- Load Manifest + resolve evidence ---
    try:
        manifest = manifest_mod.load_manifest(Path(args.manifest).expanduser().resolve())
    except manifest_mod.ManifestReadError as exc:
        print(f"ERROR: failed to load manifest: {exc}", file=sys.stderr)
        return 2

    evidence_ids = list(args.evidence) if args.evidence else list(plan.fm.get("consumed_assets") or [])
    # Filter to only ids that exist in manifest
    evidence_records = manifest.by_ids(evidence_ids)
    evidence_ids = [r["id"] for r in evidence_records]
    if len(evidence_ids) < 2:
        # We need ≥ 2 evidence per Pattern schema. If fewer, we could fall back
        # to all manifest assets matching direction.referenced_assets, etc.
        # But it's important the user knows: archive needs evidence.
        ref_in_dir = list(direction.get("referenced_assets") or [])
        extra = [aid for aid in ref_in_dir if aid not in evidence_ids and manifest.get(aid)]
        evidence_ids.extend(extra)
    if len(evidence_ids) < 2:
        print(f"ERROR: need ≥ 2 evidence assets, got {len(evidence_ids)}. "
              f"Use --evidence to specify, or ensure plan.consumed_assets has ≥ 2 entries.",
              file=sys.stderr)
        return 2
    evidence_records = manifest.by_ids(evidence_ids)

    # --- Load Prompt ---
    prompts_dir = Path(args.prompts_dir).expanduser().resolve()
    try:
        prompts = prompt_loader.load_prompts(prompts_dir)
    except prompt_loader.PromptLoadError as exc:
        print(f"ERROR: failed to load prompts: {exc}", file=sys.stderr)
        return 2
    if args.prompt_id not in prompts:
        print(f"ERROR: prompt {args.prompt_id!r} not found", file=sys.stderr)
        return 2
    prompt = prompts[args.prompt_id]

    # --- Build prompt context ---
    critique_summary = {
        "weighted_score": critique.weighted_score,
        "decision": critique.decision,
        "scores": critique.scores,
        "strengths": list(critique.fm.get("strengths") or []),
    }
    context: dict[str, Any] = {
        "project_id": project.id,
        "client": project.client,
        "project_type": project.project_type,
        "brief_summary": project.brief_summary,
        "direction": direction,
        "critique_summary": critique_summary,
        "evidence_assets": _summarize_evidence(evidence_records),
        "existing_patterns": [
            {"id": p.id, "title": p.title, "category": p.category}
            for p in existing_patterns.values()
        ],
    }

    # --- Render ---
    try:
        rendered = prompt_render.render(prompt, context)
    except prompt_render.RenderError as exc:
        print(f"ERROR: prompt render failed: {exc}", file=sys.stderr)
        return 3

    # --- Execute LLM ---
    if args.llm == "dry-run":
        llm_output = _execute_dry_run(rendered, direction, project.project_type)
        llm_mode = "dry-run"
    elif args.llm == "hook":
        if not args.llm_hook:
            print("ERROR: --llm hook requires --llm-hook PATH", file=sys.stderr)
            return 2
        try:
            llm_output = _execute_hook(rendered, Path(args.llm_hook).expanduser().resolve())
            llm_mode = "hook"
        except Exception as exc:
            print(f"ERROR: hook failed: {exc}", file=sys.stderr)
            return 1
    else:
        print(f"ERROR: unsupported llm mode {args.llm!r}", file=sys.stderr)
        return 2

    # --- Build Pattern ---
    slug = (llm_output.get("slug")
            or re.sub(r"[^a-z0-9_]+", "_", str(llm_output.get("title", "pattern")).lower()))
    pattern_id = _make_pattern_id(slug, project.id)
    if pattern_id in existing_patterns:
        # Disambiguate by appending project-derived suffix
        fallback_suffix = re.sub(r"[^a-z0-9_]+", "_", project.id.removeprefix("prj_"))[:20]
        pattern_id = _make_pattern_id(f"{slug}_{fallback_suffix}", project.id)
        if pattern_id in existing_patterns:
            print(f"ERROR: pattern slug clash; refusing to overwrite {pattern_id!r}", file=sys.stderr)
            return 4

    derived_runs = [
        critique.source_run_id,  # critic run
        plan.fm.get("source_run_id"),  # design-run
        run_id,  # this archive run
    ]
    derived_runs = [r for r in derived_runs if r]

    pattern_fm = build_pattern_fm(
        pattern_id=pattern_id,
        project=project,
        plan=plan,
        direction=direction,
        critique=critique,
        llm_output=llm_output,
        evidence_asset_ids=evidence_ids,
        archive_run_id=run_id,
        now=_now_iso(),
        derived_runs=derived_runs,
    )

    # --- Validate Pattern ---
    try:
        schema.validate(pattern_fm, "pattern")
    except schema.SchemaError as exc:
        errors.append({"level": "error" if args.strict else "warning",
                       "code": "pattern_schema_invalid",
                       "target": pattern_id, "message": str(exc)})
        if args.strict:
            print(f"ERROR: pattern schema invalid: {exc}", file=sys.stderr)
            return 4

    # --- Write Pattern ---
    pattern_path = patterns_dir / f"{pattern_id}.md"
    frontmatter.write(pattern_path, pattern_fm, pattern_note_body(pattern_fm, direction))
    pattern_jsonl = patterns_dir / f"{pattern_id}.jsonl"
    pattern_jsonl.write_text(json.dumps(pattern_fm, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- Update upstream entities ---
    entities_updated: list[str] = []

    # Plan
    if not args.no_update_plan:
        try:
            plan_changes = entity_updater.update_plan_on_archive(
                plan_path,
                pattern_id=pattern_id,
                adopted_direction_id=direction_id,
                archive_run_id=run_id,
            )
            update_log["plan"] = plan_changes
            if plan_changes:
                entities_updated.append(plan.id)
        except Exception as exc:
            errors.append({"level": "warning", "code": "plan_update_failure",
                           "target": plan.id, "message": str(exc)})

    # Project
    if not args.no_update_project:
        try:
            changed = entity_updater.update_project_on_archive(
                project_path, pattern_id=pattern_id
            )
            update_log["project"] = {"derived_pattern_refs_added": changed}
            if changed:
                entities_updated.append(project.id)
        except Exception as exc:
            errors.append({"level": "warning", "code": "project_update_failure",
                           "target": project.id, "message": str(exc)})

    # Asset notes
    if not args.no_update_assets and args.asset_notes_dir:
        notes_dir = Path(args.asset_notes_dir).expanduser().resolve()
        try:
            asset_changes = entity_updater.update_assets_on_archive(
                notes_dir, asset_ids=evidence_ids, pattern_id=pattern_id,
            )
            update_log["assets"] = asset_changes
            for aid, ch in asset_changes.items():
                if ch:
                    entities_updated.append(aid)
        except Exception as exc:
            errors.append({"level": "warning", "code": "asset_update_failure",
                           "target": "", "message": str(exc)})
    elif not args.no_update_assets:
        update_log["assets"] = "skipped (no --asset-notes-dir)"

    # --- Build Run ---
    finished = datetime.now(timezone.utc)
    metrics = {
        "evidence_asset_count": len(evidence_ids),
        "entities_updated_count": len(entities_updated),
        "elapsed_perf_seconds": round(time.perf_counter() - started_perf, 4),
    }
    inputs = {
        "critique_path": str(critique_path),
        "plan_path": str(plan_path),
        "project_path": str(project_path),
        "manifest_path": str(Path(args.manifest).expanduser().resolve()),
        "patterns_dir": str(patterns_dir),
        "prompts_dir": str(prompts_dir),
        "prompt_id": args.prompt_id,
        "out_path": str(out_dir),
        "llm_mode": args.llm,
        "evidence_override": args.evidence,
    }
    has_error = any(e.get("level") == "error" for e in errors)
    outcome = "failure" if has_error else ("partial" if errors else "success")

    run_fm = build_run_fm(
        run_id=run_id,
        started=started, finished=finished,
        inputs=inputs,
        project_id=project.id,
        parent_run_id=parent_run_id,
        rendered=rendered,
        pattern_id=pattern_id,
        pattern_path=pattern_path,
        entities_updated=entities_updated,
        update_log=update_log,
        llm_mode=llm_mode,
        metrics=metrics,
        errors=errors,
        outcome=outcome,
    )
    try:
        schema.validate(run_fm, "run")
    except schema.SchemaError as exc:
        print(f"WARNING: run record failed schema: {exc}", file=sys.stderr)

    run_path = out_dir / f"{run_id}.md"
    frontmatter.write(run_path, run_fm, run_note_body(run_fm))

    # --- Summary ---
    print(f"Critique:           {critique.id} (decision: {critique.decision})")
    print(f"Plan:               {plan.id}")
    print(f"Direction:          {direction_id} ({direction.get('name', '')})")
    print(f"Project:            {project.id}")
    print(f"Parent run:         {parent_run_id}")
    print(f"Run id:             {run_id}")
    print(f"Pattern created:    {pattern_id}")
    print(f"Title:              {pattern_fm['title']}")
    print(f"reuse_score:        {pattern_fm['reuse_score']}")
    print(f"Evidence assets:    {len(evidence_ids)}")
    print(f"Entities updated:   {len(entities_updated)} ({', '.join(entities_updated[:3])}{'...' if len(entities_updated) > 3 else ''})")
    print(f"LLM mode:           {llm_mode}")
    print(f"Outcome:            {outcome}")
    print(f"  pattern: {pattern_path}")
    print(f"  run:     {run_path}")
    if errors:
        print(f"  warnings/errors: {len(errors)}")

    return 0 if outcome != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
