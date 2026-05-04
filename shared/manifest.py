"""Manifest reader.

Reads JSONL manifests produced by design-ingest and exposes:
  - all assets indexed by id
  - filter helpers (by category, by family, by id list)
  - run-id provenance (from first record's source_run_id)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ManifestReadError(ValueError):
    pass


class Manifest:
    def __init__(self, records: list[dict[str, Any]], source_path: Path):
        self.records = records
        self.source_path = source_path
        self._by_id: dict[str, dict[str, Any]] = {r["id"]: r for r in records}

    def get(self, asset_id: str) -> dict[str, Any] | None:
        return self._by_id.get(asset_id)

    def by_ids(self, asset_ids: list[str]) -> list[dict[str, Any]]:
        return [self._by_id[aid] for aid in asset_ids if aid in self._by_id]

    def by_category(self, category: str) -> list[dict[str, Any]]:
        return [r for r in self.records if r.get("category") == category]

    def all_ids(self) -> list[str]:
        return [r["id"] for r in self.records]

    def source_run_id(self) -> str | None:
        """Return the source_run_id of the first record (ingest provenance)."""
        if not self.records:
            return None
        return self.records[0].get("source_run_id")

    def __len__(self) -> int:
        return len(self.records)


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        raise ManifestReadError(f"manifest not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ManifestReadError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            if obj.get("type") != "asset":
                continue
            if "id" not in obj:
                raise ManifestReadError(f"{path}:{lineno}: missing 'id' in record")
            records.append(obj)
    return Manifest(records, path)
