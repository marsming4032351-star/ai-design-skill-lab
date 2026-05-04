"""Project loader.

Loads a Project entity from disk. design-run depends on Project being
authored by humans (or by a future kickoff skill); this loader does not
create projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import frontmatter


class ProjectLoadError(ValueError):
    pass


class Project:
    def __init__(self, fm: dict[str, Any], body: str, source_path: Path):
        self.fm = fm
        self.body = body
        self.source_path = source_path

    @property
    def id(self) -> str:
        return self.fm["id"]

    @property
    def stage(self) -> str:
        return self.fm["stage"]

    @property
    def status(self) -> str:
        return self.fm["status"]

    @property
    def client(self) -> str:
        return self.fm.get("client", "")

    @property
    def project_type(self) -> str:
        return self.fm["project_type"]

    @property
    def brief_summary(self) -> str:
        return self.fm.get("brief_summary", "")

    @property
    def deliverables(self) -> list[dict[str, Any]]:
        return list(self.fm.get("deliverables") or [])

    @property
    def asset_refs(self) -> list[str]:
        return list(self.fm.get("asset_refs") or [])

    @property
    def pattern_refs(self) -> list[str]:
        return list(self.fm.get("pattern_refs") or [])

    @property
    def open_questions(self) -> list[str]:
        return list(self.fm.get("open_questions") or [])

    @property
    def prompt_overrides(self) -> dict[str, dict[str, Any]]:
        return dict(self.fm.get("prompt_overrides") or {})

    @property
    def run_history(self) -> list[str]:
        return list(self.fm.get("run_history") or [])


def load_project(project_md_path: Path) -> Project:
    if not project_md_path.exists():
        raise ProjectLoadError(f"project file not found: {project_md_path}")
    fm, body = frontmatter.read(project_md_path)
    if not fm or fm.get("type") != "project":
        raise ProjectLoadError(f"{project_md_path}: not a project entity (type != 'project')")
    for required in ("id", "stage", "status", "project_type", "brief_summary", "deliverables"):
        if required not in fm:
            raise ProjectLoadError(f"{project_md_path}: missing required field {required!r}")
    return Project(fm, body, project_md_path)


def append_run_to_history(project_md_path: Path, run_id: str) -> None:
    """Append run_id to project.run_history. Used by design-run after success."""
    fm, body = frontmatter.read(project_md_path)
    history = list(fm.get("run_history") or [])
    if run_id in history:
        return  # idempotent
    history.append(run_id)
    fm["run_history"] = history
    fm["updated_at"] = _now_iso()
    frontmatter.write(project_md_path, fm, body)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
