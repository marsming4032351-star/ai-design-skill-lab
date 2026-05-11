#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.obsidian_staging import create_staging_note


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture links, text, GitHub repos, prompts, and image notes into Obsidian staging Markdown."
    )
    parser.add_argument("--input", required=True, help="Link, image description, article body, GitHub repo URL, or raw note text.")
    parser.add_argument("--title", default=None, help="Optional note title. If omitted, inferred from input/source.")
    parser.add_argument("--source", default="", help="Original source URL or short source label.")
    parser.add_argument("--out", type=Path, default=ROOT / "00_Inbox_Staging", help="Output staging directory.")
    parser.add_argument("--dry-run", action="store_true", help="Mark the generated note as dry-run output. No API calls are made.")
    args = parser.parse_args()

    note_path = create_staging_note(
        content=args.input,
        out_dir=args.out,
        title=args.title,
        source=args.source,
        dry_run=args.dry_run,
    )
    print(f"created={note_path}")
    print(f"dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
