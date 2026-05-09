#!/usr/bin/env python3
"""Run a minimal HarnessRuntime demo from a YAML goal file."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import json
import sys
from pathlib import Path
from typing import Any

import yaml


_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from harness.registry import SkillRegistry  # noqa: E402
from harness.runtime import HarnessRuntime  # noqa: E402
from harness.task import TaskSpec  # noqa: E402


def load_goal(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"goal file {path} must contain a mapping")
    return data


def task_from_goal(goal: dict[str, Any]) -> TaskSpec:
    task_id = str(goal.get("id") or "task_harness_demo")
    skill_id = str(goal.get("skill_id") or "design-harness")
    inputs = goal.get("inputs") or {}
    metadata = goal.get("metadata") or {}
    if not isinstance(inputs, dict):
        raise ValueError("goal inputs must be a mapping")
    if not isinstance(metadata, dict):
        raise ValueError("goal metadata must be a mapping")
    inputs = dict(inputs)
    if "max_retries" in goal and "max_retries" not in inputs:
        inputs["max_retries"] = goal["max_retries"]
    return TaskSpec(
        id=task_id,
        skill_id=skill_id,
        inputs=inputs,
        requires_review=bool(goal.get("requires_review", False)),
        metadata=metadata,
    )


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def print_section(label: str, value: Any) -> None:
    print(f"{label}:")
    print(json.dumps(to_jsonable(value), ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the mock HarnessRuntime demo.")
    parser.add_argument("goal", help="Path to harness goal YAML")
    args = parser.parse_args(argv)

    goal_path = Path(args.goal).expanduser().resolve()
    try:
        goal = load_goal(goal_path)
        task = task_from_goal(goal)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    workspace = Path(goal.get("workspace") or "output/harness_demo")
    if not workspace.is_absolute():
        workspace = (_ROOT / workspace).resolve()

    runtime = HarnessRuntime(registry=SkillRegistry())
    context = runtime.run(task, workspace=workspace)

    print(f"run_id: {context.run_id}")
    print(f"review_required: {str(task.requires_review).lower()}")
    print(f"retry_count: {context.retry_count}")
    print(f"max_retries: {context.max_retries}")
    print(f"final_state: {context.state.get('final_state', '')}")
    print_section("final state", context.state)
    print_section("step_history", context.step_history)
    print_section("event_log", context.event_log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
