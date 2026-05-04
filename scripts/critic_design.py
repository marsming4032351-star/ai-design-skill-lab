#!/usr/bin/env python3
"""design-critic skill — score a Plan direction against a rubric.

Pipeline:
  1. Load Plan; pick target direction
  2. Load Project (for context) and rubric Rule
  3. Load Prompt (default: prm_critic_concept)
  4. Build prompt context (incl. peer_directions for differentiation)
  5. Render prompt → RenderedPrompt
  6. Execute LLM mode:
       - dry-run: return deterministic stub scores
       - hook   : invoke external script
  7. Apply rubric_engine → weighted_score + decision
  8. Validate Critique vs schema
  9. Write Critique note + JSONL
 10. Write Run log; optionally update Plan.status

Standard library only. design-critic does NOT modify Plan.directions or scores.
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
    frontmatter, plan_loader, project_loader,
    prompt_loader, prompt_render,
    rule_loader, rubric_engine,
    schema,
)


SKILL_VERSION = "0.1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_run_id(now: datetime) -> str:
    return f"run_critic_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"


def _make_critique_id(target_short: str, now: datetime) -> str:
    return f"crt_{target_short}_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"


def _canonical_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# LLM modes
# ---------------------------------------------------------------------------

def _execute_dry_run(rendered: prompt_render.RenderedPrompt,
                     rubric: rule_loader.Rule) -> dict[str, Any]:
    """Produce deterministic stub scores. Designed to be MIXED quality
    so the rubric_engine returns 'revise' (not pass/fail) by default —
    proves the engine actually reads scores, not a constant."""
    dimensions = rubric.body.get("dimensions") or []
    # Vary scores across dimensions: 4, 4, 3, 3, 2, 4
    seed_pattern = [4, 4, 3, 3, 2, 4]
    scores: dict[str, dict[str, Any]] = {}
    for i, dim in enumerate(dimensions):
        score = seed_pattern[i % len(seed_pattern)]
        scores[dim["id"]] = {
            "score": score,
            "rationale": f"(dry-run stub) 维度 {dim['id']} 评分 {score}",
        }
    return {
        "scores": scores,
        "strengths": ["(dry-run) 方向定位清晰"],
        "weaknesses": ["(dry-run) 工艺潜力维度需要更具体证据"],
        "actionable_feedback": ["(dry-run) 补充 1-2 个具体执行参考"],
        "_dry_run": True,
    }


def _execute_hook(rendered: prompt_render.RenderedPrompt, hook_path: Path) -> dict[str, Any]:
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
# Build Critique
# ---------------------------------------------------------------------------

def build_critique_fm(
    *,
    critique_id: str,
    plan: plan_loader.Plan,
    direction: dict[str, Any],
    rubric: rule_loader.Rule,
    rubric_result: rubric_engine.RubricResult,
    rendered: prompt_render.RenderedPrompt | None,
    llm_output: dict[str, Any],
    llm_mode: str,
    run_id: str,
    now: str,
) -> dict[str, Any]:
    scores_fm = [
        {
            "dimension_id": s.dimension_id,
            "label": s.label,
            "score": s.score,
            "weight": s.weight,
            "rationale": s.rationale,
        }
        for s in rubric_result.scores
    ]
    return {
        "id": critique_id,
        "type": "critique",
        "schema_version": "1.0",
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "created_by": "skill:design-critic",
        "source_run_id": run_id,
        "tags": ["design-critic", plan.stage],
        "target_type": "plan_direction",
        "target_plan_id": plan.id,
        "target_direction_id": direction.get("id"),
        "project_id": plan.project_id,
        "rubric_id": rubric.id,
        "rubric_version": rubric.version,
        "prompt_id": rendered.prompt_id if rendered else None,
        "prompt_version": rendered.prompt_version if rendered else None,
        "prompt_inputs_hash": rendered.inputs_hash if rendered else None,
        "scores": scores_fm,
        "weighted_score": rubric_result.weighted_score,
        "decision": rubric_result.decision,
        "decision_rationale": rubric_result.decision_rationale,
        "strengths": list(llm_output.get("strengths") or []),
        "weaknesses": list(llm_output.get("weaknesses") or []),
        "actionable_feedback": list(llm_output.get("actionable_feedback") or []),
        "llm_mode": llm_mode,
        "replaces": None,
        "replaced_by": None,
    }


def critique_note_body(fm: dict[str, Any], plan: plan_loader.Plan,
                       direction: dict[str, Any]) -> str:
    decision_emoji = {"pass": "✓", "revise": "○", "fail": "✗"}.get(fm["decision"], "?")
    lines = [
        f"# Critique · {direction.get('name', '?')} · {decision_emoji} {fm['decision']}",
        "",
        f"- Target: [[{plan.id}]] / direction `{direction.get('id')}`",
        f"- Project: {fm['project_id']}",
        f"- Rubric: {fm['rubric_id']} v{fm['rubric_version']}",
        f"- LLM mode: {fm['llm_mode']}",
        f"- weighted_score: **{fm['weighted_score']}**",
        "",
        "## Decision",
        f"**{fm['decision']}** — {fm['decision_rationale']}",
        "",
        "## Scores",
        "",
        "| Dimension | Weight | Score | Rationale |",
        "|---|---:|---:|---|",
    ]
    for s in fm["scores"]:
        rat = (s.get("rationale") or "").replace("\n", " ").replace("|", "\\|")
        lines.append(
            f"| {s['label']} ({s['dimension_id']}) | {s['weight']} | {s['score']} | {rat} |"
        )
    lines.append("")

    if fm.get("strengths"):
        lines.append("## Strengths")
        for s in fm["strengths"]:
            lines.append(f"- {s}")
        lines.append("")

    if fm.get("weaknesses"):
        lines.append("## Weaknesses")
        for w in fm["weaknesses"]:
            lines.append(f"- {w}")
        lines.append("")

    if fm.get("actionable_feedback"):
        lines.append("## Actionable Feedback")
        for a in fm["actionable_feedback"]:
            lines.append(f"- [ ] {a}")
        lines.append("")

    return "\n".join(lines)


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
    rubric: rule_loader.Rule,
    rendered: prompt_render.RenderedPrompt | None,
    critique_id: str,
    critique_path: Path,
    decision: str,
    llm_mode: str,
    metrics: dict[str, Any],
    errors: list[dict[str, Any]],
    outcome: str,
) -> dict[str, Any]:
    started_iso = started.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    finished_iso = finished.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    duration_ms = int((finished - started).total_seconds() * 1000)
    next_skill = "design-archive" if decision == "pass" else None
    return {
        "id": run_id,
        "type": "run",
        "schema_version": "1.0",
        "created_at": started_iso,
        "updated_at": finished_iso,
        "status": "active",
        "created_by": "skill:design-critic",
        "source_run_id": None,
        "tags": ["critic"],
        "skill": "design-critic",
        "skill_version": SKILL_VERSION,
        "started_at": started_iso,
        "finished_at": finished_iso,
        "duration_ms": duration_ms,
        "outcome": outcome,
        "parent_run_id": parent_run_id,
        "project_id": project_id,
        "inputs": inputs,
        "inputs_hash": _canonical_hash(inputs),
        "rules_used": [{"id": rubric.id, "version": rubric.version}],
        "prompts_used": (
            [
                {
                    "id": rendered.prompt_id,
                    "version": rendered.prompt_version,
                    "inputs_hash": rendered.inputs_hash,
                    "llm_mode": llm_mode,
                }
            ]
            if rendered
            else []
        ),
        "outputs": [
            {"kind": "file", "path": str(critique_path), "role": "primary"},
            {"kind": "entity", "entity_id": critique_id, "action": "created"},
        ],
        "entities_created": [critique_id],
        "entities_updated": [],
        "metrics": metrics,
        "errors": errors,
        "decision": decision,
        "next_eligible_skill": next_skill,
    }


def run_note_body(fm: dict[str, Any]) -> str:
    m = fm["metrics"]
    return (
        f"# Run · design-critic · {fm['started_at']}\n\n"
        f"- Project: {fm['project_id']}\n"
        f"- Parent run: {fm.get('parent_run_id') or '(none)'}\n"
        f"- Outcome: {fm['outcome']}\n"
        f"- Duration: {fm['duration_ms']} ms\n"
        f"- Critique: {fm['entities_created'][0]}\n"
        f"- Decision: **{fm['decision']}**\n"
        f"- weighted_score: {m.get('weighted_score', 0)}\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="design-critic skill — score a Plan direction.")
    parser.add_argument("--plan", required=True, help="Path to plan .md")
    parser.add_argument("--project", required=True, help="Path to project .md")
    parser.add_argument("--direction", required=True,
                        help="direction id within the Plan (e.g. dir_001)")
    parser.add_argument("--rubric-id", default="rul_score_concept_direction",
                        help="Rule id to use as rubric")
    parser.add_argument("--rules-dir", required=True)
    parser.add_argument("--prompt-id", default="prm_critic_concept")
    parser.add_argument("--prompts-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--llm", choices=["dry-run", "hook"], default="dry-run")
    parser.add_argument("--llm-hook", help="Path to executable hook (required if --llm hook)")
    parser.add_argument("--update-plan", action="store_true",
                        help="If decision=pass, update Plan.status from draft to reviewed")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    run_id = _make_run_id(started)

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []

    # --- Load Plan ---
    plan_path = Path(args.plan).expanduser().resolve()
    try:
        plan = plan_loader.load_plan(plan_path)
    except plan_loader.PlanLoadError as exc:
        print(f"ERROR: failed to load plan: {exc}", file=sys.stderr)
        return 2
    direction = plan.get_direction(args.direction)
    if not direction:
        print(f"ERROR: direction {args.direction!r} not found in plan {plan.id}", file=sys.stderr)
        return 2

    # --- Establish parent run (the design-run that produced the Plan) ---
    parent_run_id = plan.fm.get("source_run_id")
    if not parent_run_id:
        print("ERROR: plan has no source_run_id; cannot establish parent.", file=sys.stderr)
        return 2

    # --- Load Project (for context only) ---
    project_path = Path(args.project).expanduser().resolve()
    try:
        project = project_loader.load_project(project_path)
    except project_loader.ProjectLoadError as exc:
        print(f"ERROR: failed to load project: {exc}", file=sys.stderr)
        return 2
    if project.id != plan.project_id:
        print(f"ERROR: project id {project.id} does not match plan.project_id {plan.project_id}",
              file=sys.stderr)
        return 2

    # --- Load Rubric (Rule) ---
    rules_dir = Path(args.rules_dir).expanduser().resolve()
    try:
        rules = rule_loader.load_rules(rules_dir)
    except rule_loader.RuleLoadError as exc:
        print(f"ERROR: failed to load rules: {exc}", file=sys.stderr)
        return 2
    if args.rubric_id not in rules:
        print(f"ERROR: rubric {args.rubric_id!r} not found in {rules_dir}", file=sys.stderr)
        return 2
    rubric = rules[args.rubric_id]
    if rubric.engine != "weighted":
        print(f"ERROR: rubric {rubric.id!r} engine is {rubric.engine!r}, expected 'weighted'",
              file=sys.stderr)
        return 2

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
    context: dict[str, Any] = {
        "project_id": project.id,
        "client": project.client,
        "brief_summary": project.brief_summary,
        "project_type": project.project_type,
        "deliverables": project.deliverables,
        "direction": direction,
        "peer_directions": plan.peer_directions(args.direction),
        "rubric": rubric.body,
        "pattern_refs": project.pattern_refs,
    }

    # --- Render ---
    try:
        rendered = prompt_render.render(prompt, context)
    except prompt_render.RenderError as exc:
        print(f"ERROR: prompt render failed: {exc}", file=sys.stderr)
        return 3

    # --- Execute LLM ---
    if args.llm == "dry-run":
        llm_output = _execute_dry_run(rendered, rubric)
        llm_mode = "dry-run"
    elif args.llm == "hook":
        if not args.llm_hook:
            print("ERROR: --llm hook requires --llm-hook PATH", file=sys.stderr)
            return 2
        try:
            llm_output = _execute_hook(rendered, Path(args.llm_hook).expanduser().resolve())
            llm_mode = "hook"
        except Exception as exc:
            errors.append({"level": "error", "code": "llm_hook_failure",
                           "target": "", "message": str(exc)})
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    else:
        print(f"ERROR: unsupported llm mode {args.llm!r}", file=sys.stderr)
        return 2

    # --- Apply rubric ---
    raw_scores = llm_output.get("scores") or {}
    try:
        rubric_result = rubric_engine.apply_rubric(rubric, raw_scores)
    except rubric_engine.RubricError as exc:
        print(f"ERROR: rubric application failed: {exc}", file=sys.stderr)
        errors.append({"level": "error", "code": "rubric_failure",
                       "target": rubric.id, "message": str(exc)})
        return 4

    # --- Build Critique ---
    now_str = _now_iso()
    target_short = (args.direction or "unknown")[:16]
    critique_id = _make_critique_id(target_short, started)
    critique_fm = build_critique_fm(
        critique_id=critique_id,
        plan=plan,
        direction=direction,
        rubric=rubric,
        rubric_result=rubric_result,
        rendered=rendered,
        llm_output=llm_output,
        llm_mode=llm_mode,
        run_id=run_id,
        now=now_str,
    )

    # --- Validate Critique ---
    try:
        schema.validate(critique_fm, "critique")
    except schema.SchemaError as exc:
        errors.append({"level": "error" if args.strict else "warning",
                       "code": "critique_schema_invalid",
                       "target": critique_id, "message": str(exc)})
        if args.strict:
            print(f"ERROR: critique schema invalid: {exc}", file=sys.stderr)
            return 4

    # --- Write Critique ---
    critique_path = out_dir / f"{critique_id}.md"
    frontmatter.write(critique_path, critique_fm, critique_note_body(critique_fm, plan, direction))
    critique_jsonl = out_dir / f"{critique_id}.jsonl"
    critique_jsonl.write_text(json.dumps(critique_fm, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- Write prompt snapshot ---
    snapshot = out_dir / f"{critique_id}.prompt.txt"
    snapshot.write_text(
        f"# Prompt snapshot — {rendered.prompt_id} v{rendered.prompt_version}\n"
        f"# inputs_hash: {rendered.inputs_hash}\n\n"
        f"--- SYSTEM ---\n{rendered.system or '(none)'}\n\n"
        f"--- USER ---\n{rendered.user}\n",
        encoding="utf-8",
    )

    # --- Update Plan.status (opt-in) ---
    if args.update_plan and rubric_result.decision == "pass" and plan.status == "draft":
        try:
            plan_loader.update_plan_status(
                plan_path,
                "reviewed",
                set_decision_notes=(
                    f"critique {critique_id} (decision=pass, score={rubric_result.weighted_score})"
                ),
            )
        except Exception as exc:
            errors.append({"level": "warning", "code": "plan_update_failure",
                           "target": plan.id, "message": str(exc)})

    # --- Build Run record ---
    finished = datetime.now(timezone.utc)
    metrics = {
        "weighted_score": rubric_result.weighted_score,
        "decision": rubric_result.decision,
        "scored_dimensions": len(rubric_result.scores),
        "elapsed_perf_seconds": round(time.perf_counter() - started_perf, 4),
    }
    inputs = {
        "plan_path": str(plan_path),
        "project_path": str(project_path),
        "direction_id": args.direction,
        "rubric_id": args.rubric_id,
        "rules_dir": str(rules_dir),
        "prompts_dir": str(prompts_dir),
        "prompt_id": args.prompt_id,
        "out_path": str(out_dir),
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
        rubric=rubric,
        rendered=rendered,
        critique_id=critique_id,
        critique_path=critique_path,
        decision=rubric_result.decision,
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

    # --- Summary ---
    print(f"Plan:           {plan.id}")
    print(f"Direction:      {args.direction} ({direction.get('name', '')})")
    print(f"Project:        {project.id}")
    print(f"Rubric:         {rubric.id} v{rubric.version}")
    print(f"Parent run:     {parent_run_id}")
    print(f"Run id:         {run_id}")
    print(f"Critique id:    {critique_id}")
    print(f"weighted_score: {rubric_result.weighted_score}")
    print(f"Decision:       {rubric_result.decision.upper()}")
    print(f"  rationale:    {rubric_result.decision_rationale}")
    print(f"LLM mode:       {llm_mode}")
    print(f"Outcome:        {outcome}")
    print(f"  critique: {critique_path}")
    print(f"  run:      {run_path}")
    if errors:
        print(f"  warnings/errors: {len(errors)}")

    return 0 if outcome != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
