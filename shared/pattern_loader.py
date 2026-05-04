"""Pattern loader.

Reads existing Pattern entities. Used by design-archive to:
  - check for duplicate slugs
  - feed existing_patterns into the extraction prompt for related_patterns
  - increment reuse_count when a project references a Pattern
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import frontmatter


class PatternLoadError(ValueError):
    pass


class Pattern:
    def __init__(self, fm: dict[str, Any], body: str, source_path: Path):
        self.fm = fm
        self.body = body
        self.source_path = source_path

    @property
    def id(self) -> str:
        return self.fm["id"]

    @property
    def title(self) -> str:
        return self.fm.get("title", "")

    @property
    def category(self) -> str:
        return self.fm.get("category", "")

    @property
    def status(self) -> str:
        return self.fm.get("status", "draft")

    @property
    def version(self) -> str:
        return self.fm.get("pattern_version", "1.0.0")

    @property
    def reuse_count(self) -> int:
        return int(self.fm.get("reuse_count", 0))


def load_patterns(patterns_dir: Path) -> dict[str, Pattern]:
    """Load all .md Pattern entities. Returns empty dict if dir is empty/missing."""
    registry: dict[str, Pattern] = {}
    if not patterns_dir.exists() or not patterns_dir.is_dir():
        return registry
    for path in sorted(patterns_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            fm, body = frontmatter.read(path)
        except Exception as exc:
            raise PatternLoadError(f"failed to parse {path}: {exc}") from exc
        if not fm or fm.get("type") != "pattern":
            continue
        if "id" not in fm:
            raise PatternLoadError(f"{path}: pattern missing id")
        pat = Pattern(fm, body, path)
        if pat.id in registry:
            raise PatternLoadError(f"duplicate pattern id {pat.id!r}")
        registry[pat.id] = pat
    return registry


def increment_reuse_count(pattern_md_path: Path) -> int:
    """Atomically (best-effort) increment reuse_count. Returns new value."""
    fm, body = frontmatter.read(pattern_md_path)
    cur = int(fm.get("reuse_count", 0))
    new_value = cur + 1
    fm["reuse_count"] = new_value
    fm["updated_at"] = _now_iso()
    frontmatter.write(pattern_md_path, fm, body)
    return new_value


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
