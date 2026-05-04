"""JSONL manifest loader for design-ingest output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ManifestReadError(ValueError):
    pass


@dataclass
class Manifest:
    records: list[dict[str, Any]]

    def get(self, asset_id: str) -> dict[str, Any] | None:
        for record in self.records:
            if record.get("id") == asset_id:
                return record
        return None

    def by_ids(self, asset_ids: list[str]) -> list[dict[str, Any]]:
        found = []
        for asset_id in asset_ids:
            record = self.get(asset_id)
            if record is not None:
                found.append(record)
        return found

    def source_run_id(self) -> str | None:
        for record in self.records:
            value = record.get("source_run_id") or record.get("ingest_run_id")
            if isinstance(value, str) and value:
                return value
        return None


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        raise ManifestReadError(f"manifest does not exist: {path}")

    records: list[dict[str, Any]] = []
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ManifestReadError(f"{path}:{lineno} record must be an object")
            if "id" not in record and "sha256" in record:
                record["id"] = "ast_" + str(record["sha256"])[:12]
            if "source_path" not in record:
                record["source_path"] = record.get("path") or record.get("name") or ""
            records.append(record)
    except json.JSONDecodeError as exc:
        raise ManifestReadError(f"invalid JSONL in {path}: {exc}") from exc
    return Manifest(records)

