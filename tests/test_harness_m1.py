from __future__ import annotations

from pathlib import Path

import pytest

from harness.registry import SkillRegistry
from harness.review import ReviewDecision
from harness.runtime import HarnessRuntime
from harness.task import RunContext, StepResult, TaskSpec


def test_task_spec_run_context_and_step_result_are_structured(tmp_path: Path) -> None:
    task = TaskSpec(
        id="task_run_concept",
        skill_id="design-run",
        inputs={"project": "references/10_Projects/prj_acme_q4_campaign/project.md"},
        requires_review=True,
    )
    context = RunContext(
        run_id="run_harness_test",
        workspace=tmp_path,
        artifacts_dir=tmp_path / "artifacts",
    )
    result = StepResult.success(
        task_id=task.id,
        message="planned",
        outputs={"entrypoint": "scripts/run_design.py"},
    )

    assert task.id == "task_run_concept"
    assert task.skill_id == "design-run"
    assert task.requires_review is True
    assert context.workspace == tmp_path
    assert context.artifacts_dir == tmp_path / "artifacts"
    assert result.status == "success"
    assert result.succeeded is True
    assert result.outputs["entrypoint"] == "scripts/run_design.py"


def test_skill_registry_registers_and_resolves_entrypoints() -> None:
    registry = SkillRegistry()
    registry.register(
        skill_id="design-run",
        entrypoint="scripts/run_design.py",
        description="Existing design-run CLI",
        risk_level="medium",
    )

    skill = registry.require("design-run")

    assert skill.id == "design-run"
    assert skill.entrypoint == Path("scripts/run_design.py")
    assert skill.risk_level == "medium"
    assert registry.get("missing") is None
    with pytest.raises(KeyError):
        registry.require("missing")


def test_harness_runtime_resolves_task_without_executing_pipeline(tmp_path: Path) -> None:
    registry = SkillRegistry()
    registry.register("design-run", "scripts/run_design.py", risk_level="medium")
    runtime = HarnessRuntime(registry=registry)
    task = TaskSpec(
        id="task_run_concept",
        skill_id="design-run",
        inputs={"llm": "dry-run"},
    )
    context = RunContext("run_harness_test", workspace=tmp_path, artifacts_dir=tmp_path)

    result = runtime.run_step(task, context)

    assert result == StepResult.success(
        task_id="task_run_concept",
        message="resolved design-run",
        outputs={
            "skill_id": "design-run",
            "entrypoint": "scripts/run_design.py",
            "executed": False,
        },
    )


def test_harness_runtime_stops_when_review_rejects(tmp_path: Path) -> None:
    registry = SkillRegistry()
    registry.register("design-run", "scripts/run_design.py", risk_level="medium")

    def reviewer(task: TaskSpec, context: RunContext) -> ReviewDecision:
        return ReviewDecision.reject(reason=f"{task.id} needs human changes")

    runtime = HarnessRuntime(registry=registry, reviewer=reviewer)
    task = TaskSpec("task_run_concept", "design-run", requires_review=True)
    context = RunContext("run_harness_test", workspace=tmp_path, artifacts_dir=tmp_path)

    result = runtime.run_step(task, context)

    assert result.status == "rejected"
    assert result.succeeded is False
    assert result.message == "task_run_concept needs human changes"
    assert result.outputs == {"executed": False}
