"""Mock generator stage for Harness M2."""

from __future__ import annotations

from .task import RunContext, StepResult, TaskSpec


def generate(task: TaskSpec, context: RunContext) -> StepResult:
    """Create a deterministic mock visual from the planner output."""
    plan_data = context.state.get("plan")
    if not isinstance(plan_data, dict):
        return StepResult.failure(
            task_id=f"{task.id}:generator",
            message="planner output missing",
        )

    version = context.retry_count + 1
    feedback = context.state.get("generator_feedback")
    visual = {
        "visual_id": f"visual_{plan_data['plan_id']}_v{version}",
        "source_plan_id": plan_data["plan_id"],
        "generator": "mock",
        "version": version,
        "applied_feedback": feedback,
    }
    context.state["visual"] = visual
    return StepResult.success(
        task_id=f"{task.id}:generator",
        message="generated mock visual",
        outputs={"visual": visual},
    )
