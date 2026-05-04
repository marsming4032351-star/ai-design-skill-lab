"""Critique loader.

Reads a Critique entity from disk. design-archive depends on a critique
having decision=pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import frontmatter


class CritiqueLoadError(ValueError):
    pass


class Critique:
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
    def decision(self) -> str:
        return self.fm["decision"]

    @property
    def target_plan_id(self) -> str:
        return self.fm["target_plan_id"]

    @property
    def target_direction_id(self) -> str | None:
        return self.fm.get("target_direction_id")

    @property
    def project_id(self) -> str:
        return self.fm["project_id"]

    @property
    def weighted_score(self) -> float:
        return float(self.fm["weighted_score"])

    @property
    def scores(self) -> list[dict[str, Any]]:
        return list(self.fm.get("scores") or [])

    @property
    def source_run_id(self) -> str:
        return self.fm["source_run_id"]

    def score_for(self, dimension_id: str) -> int | None:
        for s in self.scores:
            if s.get("dimension_id") == dimension_id:
                return int(s.get("score", 0))
        return None


def load_critique(critique_md_path: Path) -> Critique:
    if not critique_md_path.exists():
        raise CritiqueLoadError(f"critique file not found: {critique_md_path}")
    fm, body = frontmatter.read(critique_md_path)
    if not fm or fm.get("type") != "critique":
        raise CritiqueLoadError(f"{critique_md_path}: not a critique entity")
    for required in ("id", "decision", "target_plan_id", "project_id",
                     "weighted_score", "scores", "source_run_id"):
        if required not in fm:
            raise CritiqueLoadError(f"{critique_md_path}: missing {required!r}")
    return Critique(fm, body, critique_md_path)
