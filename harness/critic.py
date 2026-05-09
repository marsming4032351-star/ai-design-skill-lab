"""Mock critic stage for Harness M2."""

from __future__ import annotations

from .task import RunContext, StepResult, TaskSpec


def critique(task: TaskSpec, context: RunContext) -> StepResult:
    """Score the mock visual with a deterministic dry-run decision."""
    visual = context.state.get("visual")
    if not isinstance(visual, dict):
        return StepResult.failure(
            task_id=f"{task.id}:critic",
            message="visual output missing",
        )

    decisions = task.inputs.get("critic_decisions")
    if isinstance(decisions, list) and decisions:
        index = min(context.retry_count, len(decisions) - 1)
        decision = str(decisions[index])
    else:
        decision = str(task.inputs.get("critic_decision", "pass"))

    critique_data = {
        "critique_id": f"critique_{visual['visual_id']}",
        "target_visual_id": visual["visual_id"],
        "decision": decision,
        "feedback": "mock critic feedback" if decision != "pass" else "",
        "score": 4,
    }
    context.state["critique"] = critique_data
    return StepResult.success(
        task_id=f"{task.id}:critic",
        message="critiqued mock visual",
        outputs={"critique": critique_data},
    )
