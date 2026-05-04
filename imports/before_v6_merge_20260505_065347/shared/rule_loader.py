"""Rule entity loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import frontmatter


class RuleLoadError(ValueError):
    pass


@dataclass
class Rule:
    id: str
    version: str
    engine: str
    fm: dict[str, Any]
    body: dict[str, Any]
    source_path: Path


def _rule_from_path(path: Path) -> Rule | None:
    fm, _body_text = frontmatter.read(path)
    if fm.get("type") != "rule":
        return None
    rule_id = fm.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        raise RuleLoadError(f"rule {path} is missing string id")
    body = fm.get("body") or {}
    if not isinstance(body, dict):
        raise RuleLoadError(f"rule {rule_id!r} body must be a mapping")
    return Rule(
        id=rule_id,
        version=str(fm.get("rule_version") or fm.get("version") or ""),
        engine=str(fm.get("engine") or ""),
        fm=fm,
        body=body,
        source_path=path,
    )


def load_rules(root: Path) -> dict[str, Rule]:
    if not root.exists():
        raise RuleLoadError(f"rules directory does not exist: {root}")
    if root.is_file():
        paths = [root]
    else:
        paths = sorted(root.rglob("*.md"))

    rules: dict[str, Rule] = {}
    for path in paths:
        rule = _rule_from_path(path)
        if rule is None:
            continue
        if rule.id in rules:
            raise RuleLoadError(f"duplicate rule id {rule.id!r}: {path}")
        rules[rule.id] = rule
    return rules

