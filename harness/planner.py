"""Mock planner stage for Harness M2."""

from __future__ import annotations

from .task import RunContext, StepResult, TaskSpec


def plan(task: TaskSpec, context: RunContext) -> StepResult:
    """Create a deterministic mock plan and store it on the run context."""
    plan_data = {
        "plan_id": f"plan_{task.id}",
        "brief": str(task.inputs.get("brief", "")),
        "mode": str(task.inputs.get("llm", "dry-run")),
    }
    context.state["plan"] = plan_data
    return StepResult.success(
        task_id=f"{task.id}:planner",
        message="planned mock design task",
        outputs={"plan": plan_data},
    )
