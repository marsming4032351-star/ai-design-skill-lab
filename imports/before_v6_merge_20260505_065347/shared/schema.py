"""Small runtime schema checks for design-run entities."""

from __future__ import annotations

from typing import Any


class SchemaError(ValueError):
    pass


_REQUIRED = {
    "plan": ["id", "type", "project_id", "stage", "directions", "consumed_assets", "consumed_patterns"],
    "run": ["id", "type", "skill", "project_id", "inputs", "outputs", "outcome"],
}


def validate(entity: dict[str, Any], kind: str) -> None:
    required = _REQUIRED.get(kind)
    if required is None:
        raise SchemaError(f"unknown schema kind {kind!r}")
    missing = [key for key in required if key not in entity]
    if missing:
        raise SchemaError(f"{kind} missing required fields: {', '.join(missing)}")
    if entity.get("type") != kind:
        raise SchemaError(f"{kind} type must be {kind!r}, got {entity.get('type')!r}")
    if kind == "plan":
        directions = entity.get("directions")
        if not isinstance(directions, list) or not directions:
            raise SchemaError("plan directions must be a non-empty list")
    if kind == "run":
        if entity.get("outcome") not in {"success", "partial", "failure"}:
            raise SchemaError("run outcome must be success, partial, or failure")
