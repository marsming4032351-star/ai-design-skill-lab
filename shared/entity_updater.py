"""Entity back-references updater.

After design-archive writes a Pattern, several upstream entities must be
updated to point AT the new Pattern. This module centralizes those updates
so the main script stays linear.

All updates are idempotent: running twice is a no-op.
All updates write through frontmatter.read/write, preserving body.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import frontmatter


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _append_unique(lst: list[Any], value: Any) -> bool:
    """Append value if not already in lst. Returns True if added."""
    if value in lst:
        return False
    lst.append(value)
    return True


# ---------------------------------------------------------------------------
# Plan: status, adopted_direction_id, derived_pattern_refs (we add)
# ---------------------------------------------------------------------------

def update_plan_on_archive(
    plan_md_path: Path,
    *,
    pattern_id: str,
    adopted_direction_id: str,
    archive_run_id: str,
) -> dict[str, bool]:
    """Update Plan after archive: status reviewed → adopted, set adopted_direction_id,
    add pattern_id to derived_pattern_refs (if Plan supports it).

    Plan schema 1.0 doesn't define derived_pattern_refs, but we store it under
    decision_notes for traceability and add a future-compatible field.

    Returns a dict of {field: changed?}.
    """
    fm, body = frontmatter.read(plan_md_path)
    changed: dict[str, bool] = {}

    if fm.get("status") == "reviewed":
        fm["status"] = "adopted"
        changed["status"] = True
    else:
        # Allow archive on draft too, but warn via the return value
        if fm.get("status") not in ("adopted",):
            fm["status"] = "adopted"
            changed["status"] = True

    if fm.get("adopted_direction_id") != adopted_direction_id:
        fm["adopted_direction_id"] = adopted_direction_id
        changed["adopted_direction_id"] = True

    notes = fm.get("decision_notes") or ""
    pattern_note = f"archive {archive_run_id} → pattern {pattern_id}"
    if pattern_note not in notes:
        fm["decision_notes"] = (notes + ("\n" if notes else "") + pattern_note).strip()
        changed["decision_notes"] = True

    if changed:
        fm["updated_at"] = _now_iso()
        frontmatter.write(plan_md_path, fm, body)
    return changed


# ---------------------------------------------------------------------------
# Project: derived_pattern_refs append (idempotent)
# ---------------------------------------------------------------------------

def update_project_on_archive(
    project_md_path: Path,
    *,
    pattern_id: str,
) -> bool:
    """Append pattern_id to project.derived_pattern_refs. Returns True if changed."""
    fm, body = frontmatter.read(project_md_path)
    refs = list(fm.get("derived_pattern_refs") or [])
    if not _append_unique(refs, pattern_id):
        return False
    fm["derived_pattern_refs"] = refs
    fm["updated_at"] = _now_iso()
    frontmatter.write(project_md_path, fm, body)
    return True


# ---------------------------------------------------------------------------
# Asset: pattern_refs append (idempotent)
# ---------------------------------------------------------------------------

def update_assets_on_archive(
    asset_notes_dir: Path,
    *,
    asset_ids: list[str],
    pattern_id: str,
) -> dict[str, bool]:
    """Append pattern_id to each Asset's pattern_refs.

    `asset_notes_dir` should contain files named `{asset_id}.md` (the
    convention used by scan_inbox --write-notes).

    If a note isn't found for an asset_id, it is skipped with a False entry.
    Returns {asset_id: changed?}.
    """
    results: dict[str, bool] = {}
    for aid in asset_ids:
        note_path = asset_notes_dir / f"{aid}.md"
        if not note_path.exists():
            results[aid] = False
            continue
        fm, body = frontmatter.read(note_path)
        refs = list(fm.get("pattern_refs") or [])
        if not _append_unique(refs, pattern_id):
            results[aid] = False
            continue
        fm["pattern_refs"] = refs
        fm["updated_at"] = _now_iso()
        frontmatter.write(note_path, fm, body)
        results[aid] = True
    return results
