"""Mock archive stage for Harness M2."""

from __future__ import annotations

from .task import RunContext, StepResult, TaskSpec


def archive(task: TaskSpec, context: RunContext) -> StepResult:
    """Archive a passing mock critique into a deterministic mock pattern."""
    visual = context.state.get("visual")
    critique = context.state.get("critique")
    if not isinstance(visual, dict) or not isinstance(critique, dict):
        return StepResult.failure(
            task_id=f"{task.id}:archive",
            message="visual or critique output missing",
        )
    if critique.get("decision") != "pass":
        return StepResult.failure(
            task_id=f"{task.id}:archive",
            message="critique did not pass",
            outputs={"decision": critique.get("decision")},
        )

    archive_data = {
        "pattern_id": f"pattern_{visual['visual_id']}",
        "source_visual_id": visual["visual_id"],
        "source_critique_id": critique["critique_id"],
    }
    context.state["archive"] = archive_data
    return StepResult.success(
        task_id=f"{task.id}:archive",
        message="archived mock pattern",
        outputs={"archive": archive_data},
    )
