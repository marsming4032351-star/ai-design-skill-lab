#!/usr/bin/env python3
"""Minimal dry-run scanner for the design-ingest skill prototype.

This script inventories files, applies lightweight filename/folder rules, and
writes a JSONL manifest plus a Markdown index. It does not move, rename, delete,
or modify source files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


CATEGORY_KEYWORDS = {
    "poster": ["poster", "海报", "keyvisual", "kv", "campaign", "event", "banner", "social", "主视觉", "活动"],
    "space": ["space", "interior", "retail", "exhibition", "booth", "store", "render", "3d", "空间", "展厅", "展陈", "门店", "效果图"],
    "soft-decoration": ["soft", "furniture", "material", "textile", "fabric", "lighting", "prop", "moodboard", "软装", "家具", "面料", "材质", "灯具"],
    "brand": ["brand", "logo", "identity", "vi", "guideline", "typography", "color", "packaging", "品牌", "标志", "字体", "色彩", "包装"],
    "proposal": ["proposal", "deck", "plan", "方案", "报价", "提案", "汇报", "presentation", "brief"],
    "process": ["draft", "v1", "v2", "rev", "sketch", "wireframe", "screenshot", "过程", "草稿", "修改", "迭代", "截图"],
    "reference": ["reference", "benchmark", "inspiration", "research", "mood", "案例", "参考", "竞品", "灵感", "资料", "调研"],
}

SKIP_DIRS = {".git", ".DS_Store", "__MACOSX", "node_modules"}


@dataclass
class AssetRecord:
    path: str
    name: str
    extension: str
    size_bytes: int
    modified: str
    mime_type: str | None
    sha256: str
    category: str
    confidence: str
    evidence: list[str]
    project: str
    needs_review: bool


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path) -> tuple[str, str, list[str], bool]:
    haystack = " ".join(part.lower() for part in path.parts)
    matches: list[tuple[str, list[str]]] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword.lower() in haystack]
        if found:
            matches.append((category, found))

    if not matches:
        return "unknown", "low", ["no keyword match"], True

    matches.sort(key=lambda item: len(item[1]), reverse=True)
    top_category, top_keywords = matches[0]
    evidence = [f"{top_category}: {', '.join(top_keywords[:5])}"]

    if len(matches) > 1 and len(matches[0][1]) == len(matches[1][1]):
        return top_category, "medium", evidence + ["multiple category signals"], True

    confidence = "high" if len(top_keywords) >= 2 else "medium"
    return top_category, confidence, evidence, confidence != "high"


def iter_files(inbox: Path):
    for path in sorted(inbox.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def build_record(path: Path, inbox: Path, project: str) -> AssetRecord:
    stat = path.stat()
    category, confidence, evidence, needs_review = classify(path.relative_to(inbox))
    mime_type, _ = mimetypes.guess_type(path.name)
    return AssetRecord(
        path=str(path),
        name=path.name,
        extension=path.suffix.lower(),
        size_bytes=stat.st_size,
        modified=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        mime_type=mime_type,
        sha256=hash_file(path),
        category=category,
        confidence=confidence,
        evidence=evidence,
        project=project,
        needs_review=needs_review,
    )


def write_manifest(records: list[AssetRecord], out_dir: Path) -> None:
    manifest = out_dir / "manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def write_index(records: list[AssetRecord], out_dir: Path, inbox: Path, project: str) -> None:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.category] = counts.get(record.category, 0) + 1

    lines = [
        "# Design Ingest Asset Index",
        "",
        f"- Project: {project or 'Unspecified'}",
        f"- Inbox: `{inbox}`",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Files scanned: {len(records)}",
        "",
        "## Counts by Category",
        "",
    ]

    for category in sorted(counts):
        lines.append(f"- {category}: {counts[category]}")

    lines.extend(["", "## Review Queue", ""])
    review_records = [record for record in records if record.needs_review]
    if review_records:
        for record in review_records:
            lines.append(f"- `{record.name}` -> {record.category} ({record.confidence}); {', '.join(record.evidence)}")
    else:
        lines.append("- No low-confidence records.")

    lines.extend(["", "## All Assets", ""])
    for record in records:
        lines.append(f"- `{record.name}` | {record.category} | {record.confidence} | `{record.sha256[:12]}`")

    (out_dir / "asset-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run design asset inbox scanner.")
    parser.add_argument("--inbox", required=True, help="Folder containing raw design files.")
    parser.add_argument("--out", required=True, help="Staging output folder for manifest and index.")
    parser.add_argument("--project", default="", help="Optional project label.")
    args = parser.parse_args()

    inbox = Path(args.inbox).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    if not inbox.exists() or not inbox.is_dir():
        raise SystemExit(f"Inbox does not exist or is not a directory: {inbox}")

    out_dir.mkdir(parents=True, exist_ok=True)
    records = [build_record(path, inbox, args.project) for path in iter_files(inbox)]
    write_manifest(records, out_dir)
    write_index(records, out_dir, inbox, args.project)

    print(f"Scanned {len(records)} files")
    print(f"Wrote {out_dir / 'manifest.jsonl'}")
    print(f"Wrote {out_dir / 'asset-index.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
