"""Project entity loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import frontmatter


class ProjectLoadError(ValueError):
    pass


@dataclass
class Project:
    id: str
    client: str
    project_type: str
    brief_summary: str
    deliverables: list[dict[str, Any]]
    open_questions: list[str]
    asset_refs: list[str]
    pattern_refs: list[str]
    prompt_overrides: dict[str, Any]
    fm: dict[str, Any]


def _string_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_project(path: Path) -> Project:
    if not path.exists():
        raise ProjectLoadError(f"project does not exist: {path}")
    fm, _body = frontmatter.read(path)
    project_id = fm.get("id")
    if not isinstance(project_id, str) or not project_id:
        raise ProjectLoadError(f"project {path} is missing string id")

    deliverables = fm.get("deliverables") or []
    if not isinstance(deliverables, list):
        raise ProjectLoadError(f"project {project_id!r} deliverables must be a list")

    prompt_overrides = fm.get("prompt_overrides") or {}
    if not isinstance(prompt_overrides, dict):
        prompt_overrides = {}

    return Project(
        id=project_id,
        client=str(fm.get("client") or ""),
        project_type=str(fm.get("project_type") or ""),
        brief_summary=str(fm.get("brief_summary") or fm.get("brief") or ""),
        deliverables=[dict(item) for item in deliverables if isinstance(item, dict)],
        open_questions=_string_list(fm.get("open_questions")),
        asset_refs=_string_list(fm.get("asset_refs") or fm.get("assets")),
        pattern_refs=_string_list(fm.get("pattern_refs") or fm.get("patterns")),
        prompt_overrides=prompt_overrides,
        fm=fm,
    )


def append_run_to_history(path: Path, run_id: str) -> None:
    fm, body = frontmatter.read(path)
    history = fm.get("run_history")
    if not isinstance(history, list):
        history = []
    history.append(run_id)
    fm["run_history"] = history
    frontmatter.write(path, fm, body)

