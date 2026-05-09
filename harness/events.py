"""Runtime event records for the Design Harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RuntimeEvent:
    """A small append-only event for harness runtime observability."""

    event_type: str
    run_id: str
    task_id: str = ""
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
