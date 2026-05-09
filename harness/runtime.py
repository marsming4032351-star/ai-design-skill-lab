"""Minimal runtime shell for Design Harness M1.

M1 deliberately resolves tasks but does not execute existing pipeline CLIs.
M2 adds a mock/dry-run lifecycle runner that orchestrates harness-native
planner, generator, critic, and archive stages.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import secrets

from . import archive as archive_stage
from . import critic as critic_stage
from . import generator as generator_stage
from . import planner as planner_stage
from .events import RuntimeEvent
from .registry import SkillRegistry
from .review import ReviewDecision
from .task import RunContext, StepResult, TaskSpec


Reviewer = Callable[[TaskSpec, RunContext], ReviewDecision]


class HarnessRuntime:
    """Resolve task specs against a registry and apply optional review gates."""

    def __init__(self, *, registry: SkillRegistry, reviewer: Reviewer | None = None) -> None:
        self.registry = registry
        self.reviewer = reviewer

    def run(self, task: TaskSpec, *, workspace: str | Path) -> RunContext:
        """Run the minimal mock design lifecycle.

        This method does not call existing pipeline CLIs. It executes only
        harness-native mock stages so M2 can validate orchestration semantics.
        """
        run_id = self._make_run_id()
        workspace_path = Path(workspace)
        context = RunContext(
            run_id=run_id,
            workspace=workspace_path,
            artifacts_dir=workspace_path / "harness_runs" / run_id,
            max_retries=self._max_retries(task),
        )
        self._event(context, "run_started", task.id, "harness run started")

        result = self._run_stage(context, task, "planner", planner_stage.plan)
        if not result.succeeded:
            context.state["final_state"] = "FAILED"
            self._event(context, "run_finished", task.id, "harness run failed")
            return context

        while True:
            result = self._run_stage(context, task, "generator", generator_stage.generate)
            if not result.succeeded:
                context.state["final_state"] = "FAILED"
                self._event(context, "run_finished", task.id, "harness run failed")
                return context

            result = self._run_stage(context, task, "critic", critic_stage.critique)
            if not result.succeeded:
                context.state["final_state"] = "FAILED"
                self._event(context, "run_finished", task.id, "harness run failed")
                return context
            if context.retry_count > 0:
                self._event(
                    context,
                    "retry_finished",
                    task.id,
                    f"retry {context.retry_count} finished",
                )

            critique = context.state.get("critique")
            decision = critique.get("decision") if isinstance(critique, dict) else None
            if decision == "pass":
                self._event(context, "critic_passed", result.task_id, "critic passed")
                break

            self._event(context, "critic_failed", result.task_id, "critic failed")
            if context.retry_count >= context.max_retries:
                context.state["final_state"] = "FAILED"
                self._event(context, "run_finished", task.id, "harness run failed")
                return context

            if isinstance(critique, dict):
                context.state["generator_feedback"] = critique.get("feedback", "")
            context.increment_retry()
            self._event(
                context,
                "retry_started",
                task.id,
                f"retry {context.retry_count} started",
            )

        archive_task = TaskSpec(
            id=f"{task.id}:archive",
            skill_id="archive",
            inputs=task.inputs,
            requires_review=True,
            metadata=task.metadata,
        )
        self._event(context, "review_requested", archive_task.id, "archive review requested")
        decision = self._review(archive_task, context)
        if not decision.approved:
            self._event(context, "review_rejected", archive_task.id, decision.reason)
            result = StepResult.rejected(
                task_id=archive_task.id,
                message=decision.reason or "review rejected",
                outputs={"executed": False},
            )
            context.record_step(result)
            context.state["final_state"] = "REVIEW_REQUIRED"
            self._event(context, "run_finished", task.id, "harness run rejected")
            return context

        self._event(context, "review_approved", archive_task.id, decision.reason)
        result = self._run_stage(context, task, "archive", archive_stage.archive)
        context.state["final_state"] = "ARCHIVED" if result.succeeded else "FAILED"
        finish_message = "harness run finished" if result.succeeded else "harness run failed"
        self._event(context, "run_finished", task.id, finish_message)
        return context

    def run_step(self, task: TaskSpec, context: RunContext) -> StepResult:
        try:
            skill = self.registry.require(task.skill_id)
        except KeyError as exc:
            return StepResult.failure(task_id=task.id, message=str(exc))

        if task.requires_review:
            decision = self._review(task, context)
            if not decision.approved:
                return StepResult.rejected(
                    task_id=task.id,
                    message=decision.reason or "review rejected",
                    outputs={"executed": False},
                )

        return StepResult.success(
            task_id=task.id,
            message=f"resolved {skill.id}",
            outputs={
                "skill_id": skill.id,
                "entrypoint": str(skill.entrypoint),
                "executed": False,
            },
        )

    def _review(self, task: TaskSpec, context: RunContext) -> ReviewDecision:
        if self.reviewer is None:
            return ReviewDecision.approve(reason="no reviewer configured")
        return self.reviewer(task, context)

    def _run_stage(
        self,
        context: RunContext,
        task: TaskSpec,
        stage_name: str,
        stage_fn: Callable[[TaskSpec, RunContext], StepResult],
    ) -> StepResult:
        stage_task_id = f"{task.id}:{stage_name}"
        self._event(context, "step_started", stage_task_id, f"{stage_name} started")
        result = stage_fn(task, context)
        context.record_step(result)
        self._event(context, "step_finished", result.task_id, result.message)
        return result

    def _event(
        self,
        context: RunContext,
        event_type: str,
        task_id: str,
        message: str = "",
    ) -> None:
        context.record_event(
            RuntimeEvent(
                event_type=event_type,
                run_id=context.run_id,
                task_id=task_id,
                message=message,
            )
        )

    def _make_run_id(self) -> str:
        now = datetime.now(timezone.utc)
        return f"run_harness_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"

    def _max_retries(self, task: TaskSpec) -> int:
        raw_value = task.inputs.get("max_retries", 1)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            return 1
        return max(value, 0)
