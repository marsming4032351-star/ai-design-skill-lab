"""Pattern entity loader and updater."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import frontmatter


class PatternLoadError(ValueError):
    pass


@dataclass
class Pattern:
    id: str
    title: str
    status: str
    fm: dict[str, Any]
    body: str
    source_path: Path


def _pattern_from_path(path: Path) -> Pattern | None:
    fm, body = frontmatter.read(path)
    if fm.get("type") != "pattern":
        return None
    pattern_id = fm.get("id")
    if not isinstance(pattern_id, str) or not pattern_id:
        raise PatternLoadError(f"pattern {path} is missing string id")
    return Pattern(
        id=pattern_id,
        title=str(fm.get("title") or pattern_id),
        status=str(fm.get("status") or "draft"),
        fm=fm,
        body=body,
        source_path=path,
    )


def load_patterns(root: Path) -> dict[str, Pattern]:
    if not root.exists():
        raise PatternLoadError(f"patterns directory does not exist: {root}")
    if root.is_file():
        paths = [root]
    else:
        paths = sorted(root.rglob("*.md"))

    patterns: dict[str, Pattern] = {}
    for path in paths:
        pattern = _pattern_from_path(path)
        if pattern is None:
            continue
        if pattern.id in patterns:
            raise PatternLoadError(f"duplicate pattern id {pattern.id!r}: {path}")
        patterns[pattern.id] = pattern
    return patterns


def increment_reuse_count(path: Path) -> int:
    fm, body = frontmatter.read(path)
    current = int(fm.get("reuse_count") or 0)
    updated = current + 1
    fm["reuse_count"] = updated
    frontmatter.write(path, fm, body)
    return updated

