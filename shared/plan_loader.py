"""Plan loader.

Reads a Plan entity from disk. design-critic depends on Plan being already
written by design-run; this loader does not create plans.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import frontmatter


class PlanLoadError(ValueError):
    pass


class Plan:
    def __init__(self, fm: dict[str, Any], body: str, source_path: Path):
        self.fm = fm
        self.body = body
        self.source_path = source_path

    @property
    def id(self) -> str:
        return self.fm["id"]

    @property
    def status(self) -> str:
        return self.fm["status"]

    @property
    def project_id(self) -> str:
        return self.fm["project_id"]

    @property
    def stage(self) -> str:
        return self.fm["stage"]

    @property
    def directions(self) -> list[dict[str, Any]]:
        return list(self.fm.get("directions") or [])

    def get_direction(self, direction_id: str) -> dict[str, Any] | None:
        for d in self.directions:
            if d.get("id") == direction_id:
                return d
        return None

    def peer_directions(self, exclude_id: str) -> list[dict[str, Any]]:
        return [d for d in self.directions if d.get("id") != exclude_id]


def load_plan(plan_md_path: Path) -> Plan:
    if not plan_md_path.exists():
        raise PlanLoadError(f"plan file not found: {plan_md_path}")
    fm, body = frontmatter.read(plan_md_path)
    if not fm or fm.get("type") != "plan":
        raise PlanLoadError(f"{plan_md_path}: not a plan entity (type != 'plan')")
    for required in ("id", "project_id", "stage", "status", "directions",
                     "source_run_id"):
        if required not in fm:
            raise PlanLoadError(f"{plan_md_path}: missing required field {required!r}")
    return Plan(fm, body, plan_md_path)


def update_plan_status(plan_md_path: Path, new_status: str,
                       *, set_decision_notes: str | None = None) -> None:
    """Update Plan.status (and optionally decision_notes) in-place.

    Used by design-critic when transitioning draft → reviewed.
    Does NOT touch directions, prompt_inputs_hash, or any immutable field.
    """
    fm, body = frontmatter.read(plan_md_path)
    fm["status"] = new_status
    if set_decision_notes is not None:
        fm["decision_notes"] = set_decision_notes
    fm["updated_at"] = _now_iso()
    frontmatter.write(plan_md_path, fm, body)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
