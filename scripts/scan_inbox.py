#!/usr/bin/env python3
"""Design Ingest scanner v2 — rule-driven, schema-validated, run-logged.

Pipeline (per file):
  1. inventory  — walk inbox, hash, mtime, size
  2. classify   — invoke shared.rule_engine.classify (router)
  3. group      — detect asset families (v1/v2/final, shared basename)
  4. build      — produce Asset frontmatter dict per schema 01_asset.md
  5. validate   — shared.schema.validate(asset_dict, "asset")
  6. emit jsonl — append to manifest.jsonl
  7. emit md    — opt-in, write per-asset notes to staging
Then write a single Run record to <out>/run.md per schema 05_run.md.

Standard library only. Default mode is dry-run-friendly: never modifies
source files, only writes into the staging --out directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import secrets
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow running as a script: ensure parent of `shared/` is on sys.path
_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from shared import frontmatter, rule_engine, rule_loader, schema  # noqa: E402


SKILL_VERSION = "0.2.0"
SKIP_DIRS = {".git", ".DS_Store", "__MACOSX", "node_modules", ".obsidian"}


# ---------------------------------------------------------------------------
# Step 1: inventory
# ---------------------------------------------------------------------------

def iter_files(inbox: Path):
    for path in sorted(inbox.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Step 3: family grouping
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"[_-](v\d+|final|draft|wip|rev\d+|tmp)\b", re.IGNORECASE)


def family_key(path: Path) -> str:
    """Strip version suffixes from basename to group variants together."""
    stem = path.stem
    stripped = _VERSION_RE.sub("", stem).strip("_- ")
    folder = path.parent.name
    return f"{folder}:{stripped or stem}".lower()


def detect_family_role(path: Path, classification_role: str | None) -> str | None:
    """Decide family role.

    Priority: classification_role (variant flag from process co-category) →
    filename keyword → original.
    """
    if classification_role:
        return classification_role
    name = path.stem.lower()
    if "final" in name:
        return "final"
    if any(tok in name for tok in ("draft", "wip", "tmp", "rev")):
        return "variant"
    if re.search(r"v\d+", name):
        return "variant"
    return "original"


# ---------------------------------------------------------------------------
# Step 4: build Asset
# ---------------------------------------------------------------------------

def build_asset_fm(
    path: Path,
    cls: rule_engine.Classification,
    project_id: str,
    run_id: str,
    family_id: str,
) -> dict[str, Any]:
    stat = path.stat()
    sha = hash_file(path)
    asset_id = f"ast_{sha[:12]}"
    mime_type, _ = mimetypes.guess_type(path.name)
    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    now = _now_iso()
    family_role = detect_family_role(path, cls.family_role)

    fm: dict[str, Any] = {
        "id": asset_id,
        "type": "asset",
        "schema_version": "1.0",
        "created_at": now,
        "updated_at": now,
        "status": "staged",
        "created_by": "skill:design-ingest",
        "source_run_id": run_id,
        "tags": ["design-asset"],
        # Asset-specific
        "category": cls.category,
        "confidence": cls.confidence,
        "needs_review": cls.needs_review,
        "evidence": list(cls.evidence) or ["no evidence"],
        "source_path": str(path),
        "source_hash": sha,
        "source_size_bytes": stat.st_size,
        "source_modified": mtime,
        "mime_type": mime_type,
        "extension": path.suffix.lower(),
        "project_refs": [project_id] if project_id else [],
        "pattern_refs": [],
        "family_id": family_id,
        "family_role": family_role,
        "derived_meta": {"thumb_path": "", "ocr_text": "", "caption": ""},
    }
    if cls.conflicts:
        fm["conflicts"] = cls.conflicts
    return fm


def asset_note_body(fm: dict[str, Any]) -> str:
    return (
        f"# {Path(fm['source_path']).stem}\n\n"
        "## Summary\n_TBD_\n\n"
        "## Classification\n"
        f"- Category: {fm['category']}\n"
        f"- Confidence: {fm['confidence']}\n"
        f"- Evidence: {'; '.join(fm['evidence'])}\n"
        f"- Needs review: {fm['needs_review']}\n\n"
        "## Source\n"
        f"- Original path: `{fm['source_path']}`\n"
        f"- Hash: `{fm['source_hash']}`\n"
        f"- Modified: {fm['source_modified']}\n"
    )


# ---------------------------------------------------------------------------
# Run record
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_run_id(skill: str, started_at: datetime) -> str:
    short = skill.replace("design-", "")
    rand = secrets.token_hex(2)
    return f"run_{short}_{started_at:%Y%m%d_%H%M%S}_{rand}"


def _canonical_inputs_hash(inputs: dict[str, Any]) -> str:
    payload = json.dumps(inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_run_fm(
    *,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    inputs: dict[str, Any],
    project_id: str,
    rules_used: list[tuple[str, str]],
    outputs: list[dict[str, Any]],
    entities_created: list[str],
    metrics: dict[str, Any],
    errors: list[dict[str, Any]],
    outcome: str,
) -> dict[str, Any]:
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    started_iso = started_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    finished_iso = finished_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    fm: dict[str, Any] = {
        "id": run_id,
        "type": "run",
        "schema_version": "1.0",
        "created_at": started_iso,
        "updated_at": finished_iso,
        "status": "active",
        "created_by": "skill:design-ingest",
        "source_run_id": None,
        "tags": ["ingest"],
        "skill": "design-ingest",
        "skill_version": SKILL_VERSION,
        "started_at": started_iso,
        "finished_at": finished_iso,
        "duration_ms": duration_ms,
        "outcome": outcome,
        "parent_run_id": None,
        "project_id": project_id or None,
        "inputs": inputs,
        "inputs_hash": _canonical_inputs_hash(inputs),
        "rules_used": [{"id": rid, "version": ver} for rid, ver in _dedup(rules_used)],
        "prompts_used": [],
        "outputs": outputs,
        "entities_created": entities_created,
        "entities_updated": [],
        "metrics": metrics,
        "errors": errors,
        "decision": None,
        "next_eligible_skill": None,
    }
    return fm


def _dedup(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def run_note_body(fm: dict[str, Any]) -> str:
    m = fm.get("metrics") or {}
    return (
        f"# Run · design-ingest · {fm['started_at']}\n\n"
        f"## Summary\n"
        f"- Project: {fm.get('project_id') or 'Unspecified'}\n"
        f"- Files scanned: {m.get('files_scanned', 0)}\n"
        f"- Outcome: {fm['outcome']}\n"
        f"- Duration: {fm['duration_ms']} ms\n\n"
        f"## Counts\n"
        f"- High: {m.get('classified_high', 0)}\n"
        f"- Medium: {m.get('classified_medium', 0)}\n"
        f"- Low: {m.get('classified_low', 0)}\n"
        f"- Unknown: {m.get('classified_unknown', 0)}\n"
        f"- Needs review: {m.get('needs_review', 0)}\n"
    )


# ---------------------------------------------------------------------------
# Asset index
# ---------------------------------------------------------------------------

def write_asset_index(records: list[dict[str, Any]], out_dir: Path, inbox: Path, project_id: str) -> Path:
    counts = Counter(r["category"] for r in records)
    review_records = [r for r in records if r["needs_review"]]
    families: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        families.setdefault(r["family_id"], []).append(r)

    lines: list[str] = [
        "# Design Ingest Asset Index",
        "",
        f"- Project: {project_id or 'Unspecified'}",
        f"- Inbox: `{inbox}`",
        f"- Generated: {_now_iso()}",
        f"- Files scanned: {len(records)}",
        "",
        "## Counts by Category",
        "",
    ]
    for category in sorted(counts):
        lines.append(f"- {category}: {counts[category]}")

    lines += ["", "## Review Queue", ""]
    if review_records:
        for r in review_records:
            lines.append(
                f"- `{Path(r['source_path']).name}` -> {r['category']} ({r['confidence']}); "
                f"{'; '.join(r['evidence'][:2])}"
            )
    else:
        lines.append("- No low-confidence records.")

    lines += ["", "## Families", ""]
    for fid, members in sorted(families.items()):
        lines.append(f"- **{fid}** ({len(members)} files)")
        for r in members:
            role = r.get("family_role") or "-"
            lines.append(
                f"  - `{Path(r['source_path']).name}` | {r['category']} | {r['confidence']} | role={role}"
            )

    out_path = out_dir / "asset-index.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Design ingest scanner v2.")
    parser.add_argument("--inbox", required=True, help="Folder containing raw design files.")
    parser.add_argument("--out", required=True, help="Staging output folder for manifest, index, and run log.")
    parser.add_argument("--rules-dir", required=True, help="Directory of Rule entities (40_Rules/).")
    parser.add_argument("--project", default="", help="Optional project ID (e.g. prj_acme_q4_campaign).")
    parser.add_argument("--write-notes", action="store_true",
                        help="Also write per-asset .md notes to <out>/notes/.")
    parser.add_argument("--strict", action="store_true",
                        help="Abort on first schema validation error (default: skip and log).")
    args = parser.parse_args()

    inbox = Path(args.inbox).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    rules_dir = Path(args.rules_dir).expanduser().resolve()

    if not inbox.exists() or not inbox.is_dir():
        print(f"ERROR: inbox does not exist or is not a directory: {inbox}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = out_dir / "notes"
    if args.write_notes:
        notes_dir.mkdir(exist_ok=True)

    started_at = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    run_id = _make_run_id("design-ingest", started_at)

    # Load rules
    try:
        registry = rule_loader.load_rules(rules_dir)
    except rule_loader.RuleLoadError as exc:
        print(f"ERROR: failed to load rules: {exc}", file=sys.stderr)
        return 3

    classification_active = [
        r for r in rule_loader.filter_rules(registry, domain="classification")
        if r.engine == "keyword"
    ]
    if not classification_active:
        print("ERROR: no active classification rules found.", file=sys.stderr)
        return 3

    # Pipeline
    paths = list(iter_files(inbox))
    records: list[dict[str, Any]] = []
    rules_used_global: list[tuple[str, str]] = []
    errors: list[dict[str, Any]] = []

    # First pass — classify and build family_id
    classifications: list[tuple[Path, rule_engine.Classification]] = []
    for path in paths:
        candidate = rule_engine.AssetCandidate(path=str(path), extension=path.suffix.lower())
        cls = rule_engine.classify(candidate, registry)
        classifications.append((path, cls))
        rules_used_global.extend(cls.rules_used)

    # Group families
    family_map = {p: family_key(p) for p, _ in classifications}

    # Second pass — build, validate, emit
    manifest_path = out_dir / "manifest.jsonl"
    manifest_handle = manifest_path.open("w", encoding="utf-8")
    entities_created: list[str] = []
    seen_hashes: dict[str, str] = {}  # sha256 → first source_path (for dedup)
    duplicates_skipped = 0
    try:
        for path, cls in classifications:
            fm = build_asset_fm(path, cls, args.project, run_id, family_map[path])
            sha = fm["source_hash"]
            if sha in seen_hashes:
                duplicates_skipped += 1
                errors.append({
                    "level": "warning",
                    "code": "duplicate_source_hash",
                    "target": str(path),
                    "message": f"sha256 already seen at {seen_hashes[sha]}",
                })
                continue
            seen_hashes[sha] = str(path)
            try:
                schema.validate(fm, "asset")
            except schema.SchemaError as exc:
                errors.append({
                    "level": "error" if args.strict else "warning",
                    "code": "asset_schema_invalid",
                    "target": str(path),
                    "message": str(exc),
                })
                if args.strict:
                    raise
                continue
            records.append(fm)
            entities_created.append(fm["id"])
            manifest_handle.write(json.dumps(fm, ensure_ascii=False) + "\n")
            if args.write_notes:
                note_name = f"{fm['id']}.md"
                note_path = notes_dir / note_name
                frontmatter.write(note_path, fm, asset_note_body(fm))
    finally:
        manifest_handle.close()

    # Asset index
    index_path = write_asset_index(records, out_dir, inbox, args.project)

    # Run record
    finished_at = datetime.now(timezone.utc)
    metrics = {
        "files_scanned": len(paths),
        "assets_created": len(records),
        "classified_high": sum(1 for r in records if r["confidence"] == "high"),
        "classified_medium": sum(1 for r in records if r["confidence"] == "medium"),
        "classified_low": sum(1 for r in records if r["confidence"] == "low"),
        "classified_unknown": sum(1 for r in records if r["category"] == "unknown"),
        "needs_review": sum(1 for r in records if r["needs_review"]),
        "duplicates_skipped": duplicates_skipped,
        "elapsed_perf_seconds": round(time.perf_counter() - started_perf, 4),
    }

    outputs_log: list[dict[str, Any]] = [
        {"kind": "file", "path": str(manifest_path), "role": "primary"},
        {"kind": "file", "path": str(index_path), "role": "summary"},
    ]
    for eid in entities_created:
        outputs_log.append({"kind": "entity", "entity_id": eid, "action": "created"})

    has_error = any(e.get("level") == "error" for e in errors)
    outcome = "failure" if has_error else ("partial" if errors else "success")

    inputs = {
        "inbox_path": str(inbox),
        "out_path": str(out_dir),
        "rules_dir": str(rules_dir),
        "project_id": args.project or None,
        "write_notes": bool(args.write_notes),
        "strict": bool(args.strict),
    }

    run_fm = build_run_fm(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        inputs=inputs,
        project_id=args.project,
        rules_used=rules_used_global,
        outputs=outputs_log,
        entities_created=entities_created,
        metrics=metrics,
        errors=errors,
        outcome=outcome,
    )
    try:
        schema.validate(run_fm, "run")
    except schema.SchemaError as exc:
        print(f"ERROR: run record failed schema validation: {exc}", file=sys.stderr)
        # Still write it for debugging
    run_path = out_dir / f"{run_id}.md"
    frontmatter.write(run_path, run_fm, run_note_body(run_fm))

    print(f"Scanned {len(paths)} files")
    print(f"Created {len(records)} Asset records ({metrics['needs_review']} need review)")
    print(f"Outcome: {outcome}")
    print(f"  manifest: {manifest_path}")
    print(f"  index:    {index_path}")
    print(f"  run:      {run_path}")
    if errors:
        print(f"  warnings/errors: {len(errors)}")

    return 0 if outcome != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
