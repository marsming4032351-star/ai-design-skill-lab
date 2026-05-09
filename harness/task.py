"""Core task records for the Design Harness M1 skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskSpec:
    """A single harness step requested from a registered skill."""

    id: str
    skill_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    requires_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunContext:
    """Per-run context shared by harness steps."""

    run_id: str
    workspace: Path
    artifacts_dir: Path
    state: dict[str, Any] = field(default_factory=dict)
    step_history: list["StepResult"] = field(default_factory=list)
    event_log: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace", Path(self.workspace))
        object.__setattr__(self, "artifacts_dir", Path(self.artifacts_dir))

    def record_step(self, result: "StepResult") -> None:
        self.step_history.append(result)

    def record_event(self, event: Any) -> None:
        self.event_log.append(event)

    def increment_retry(self) -> None:
        object.__setattr__(self, "retry_count", self.retry_count + 1)


@dataclass(frozen=True)
class StepResult:
    """Result of resolving or running a harness step."""

    task_id: str
    status: str
    message: str = ""
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.status == "success"

    @classmethod
    def success(
        cls,
        *,
        task_id: str,
        message: str = "",
        outputs: dict[str, Any] | None = None,
    ) -> "StepResult":
        return cls(
            task_id=task_id,
            status="success",
            message=message,
            outputs=dict(outputs or {}),
        )

    @classmethod
    def failure(
        cls,
        *,
        task_id: str,
        message: str,
        errors: list[str] | tuple[str, ...] | None = None,
        outputs: dict[str, Any] | None = None,
    ) -> "StepResult":
        return cls(
            task_id=task_id,
            status="failure",
            message=message,
            outputs=dict(outputs or {}),
            errors=tuple(errors or (message,)),
        )

    @classmethod
    def rejected(
        cls,
        *,
        task_id: str,
        message: str,
        outputs: dict[str, Any] | None = None,
    ) -> "StepResult":
        return cls(
            task_id=task_id,
            status="rejected",
            message=message,
            outputs=dict(outputs or {}),
        )
