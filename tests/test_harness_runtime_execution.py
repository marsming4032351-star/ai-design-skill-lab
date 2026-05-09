from __future__ import annotations

from pathlib import Path

from harness.registry import SkillRegistry
from harness.review import ReviewDecision
from harness.runtime import HarnessRuntime
from harness.task import TaskSpec


def test_harness_runtime_executes_minimal_mock_design_lifecycle(tmp_path: Path) -> None:
    runtime = HarnessRuntime(registry=SkillRegistry())
    task = TaskSpec(
        id="task_design_loop",
        skill_id="design-harness",
        inputs={"brief": "高端冷感海报", "llm": "dry-run"},
    )

    context = runtime.run(task, workspace=tmp_path)

    assert context.run_id.startswith("run_harness_")
    assert [step.task_id for step in context.step_history] == [
        "task_design_loop:planner",
        "task_design_loop:generator",
        "task_design_loop:critic",
        "task_design_loop:archive",
    ]
    assert all(step.succeeded for step in context.step_history)
    assert context.state["plan"]["brief"] == "高端冷感海报"
    assert context.state["visual"]["source_plan_id"] == context.state["plan"]["plan_id"]
    assert context.state["critique"]["decision"] == "pass"
    assert context.state["archive"]["source_visual_id"] == context.state["visual"]["visual_id"]
    assert [event.event_type for event in context.event_log] == [
        "run_started",
        "step_started",
        "step_finished",
        "step_started",
        "step_finished",
        "step_started",
        "step_finished",
        "critic_passed",
        "review_requested",
        "review_approved",
        "step_started",
        "step_finished",
        "run_finished",
    ]


def test_harness_runtime_stops_archive_when_review_rejects(tmp_path: Path) -> None:
    decisions: list[str] = []

    def reviewer(task: TaskSpec, context) -> ReviewDecision:
        decisions.append(task.id)
        return ReviewDecision.reject(reason="archive needs human approval")

    runtime = HarnessRuntime(registry=SkillRegistry(), reviewer=reviewer)
    task = TaskSpec(
        id="task_design_loop",
        skill_id="design-harness",
        inputs={"brief": "高端冷感海报"},
        requires_review=True,
    )

    context = runtime.run(task, workspace=tmp_path)

    assert decisions == ["task_design_loop:archive"]
    assert [step.task_id for step in context.step_history] == [
        "task_design_loop:planner",
        "task_design_loop:generator",
        "task_design_loop:critic",
        "task_design_loop:archive",
    ]
    assert context.step_history[-1].status == "rejected"
    assert context.step_history[-1].message == "archive needs human approval"
    assert "archive" not in context.state
    assert context.event_log[-1].event_type == "run_finished"


def test_harness_runtime_retries_failed_critic_and_archives_on_second_pass(tmp_path: Path) -> None:
    runtime = HarnessRuntime(registry=SkillRegistry())
    task = TaskSpec(
        id="task_design_loop",
        skill_id="design-harness",
        inputs={
            "brief": "高端冷感海报",
            "critic_decisions": ["fail", "pass"],
            "max_retries": 1,
        },
    )

    context = runtime.run(task, workspace=tmp_path)

    assert context.retry_count == 1
    assert [step.task_id for step in context.step_history] == [
        "task_design_loop:planner",
        "task_design_loop:generator",
        "task_design_loop:critic",
        "task_design_loop:generator",
        "task_design_loop:critic",
        "task_design_loop:archive",
    ]
    assert context.state["visual"]["version"] == 2
    assert context.state["visual"]["applied_feedback"] == "mock critic feedback"
    assert context.state["critique"]["decision"] == "pass"
    assert context.state["final_state"] == "ARCHIVED"
    assert [event.event_type for event in context.event_log].count("critic_failed") == 1
    assert [event.event_type for event in context.event_log].count("critic_passed") == 1
    assert "retry_started" in [event.event_type for event in context.event_log]
    assert "retry_finished" in [event.event_type for event in context.event_log]


def test_harness_runtime_fails_after_exceeding_max_retries(tmp_path: Path) -> None:
    runtime = HarnessRuntime(registry=SkillRegistry())
    task = TaskSpec(
        id="task_design_loop",
        skill_id="design-harness",
        inputs={
            "brief": "高端冷感海报",
            "critic_decision": "fail",
            "max_retries": 1,
        },
    )

    context = runtime.run(task, workspace=tmp_path)

    assert context.retry_count == 1
    assert [step.task_id for step in context.step_history] == [
        "task_design_loop:planner",
        "task_design_loop:generator",
        "task_design_loop:critic",
        "task_design_loop:generator",
        "task_design_loop:critic",
    ]
    assert context.state["critique"]["decision"] == "fail"
    assert context.state["final_state"] == "FAILED"
    assert "archive" not in context.state
    assert [event.event_type for event in context.event_log].count("critic_failed") == 2
    assert [event.event_type for event in context.event_log].count("retry_started") == 1
    assert [event.event_type for event in context.event_log].count("retry_finished") == 1
