"""Rule loader for Design Data Factory.

Loads rule entities (Markdown + YAML frontmatter) from a rules directory.
Returns a Rule registry indexed by id, with helpers to filter by domain.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import frontmatter


class RuleLoadError(ValueError):
    pass


class Rule:
    """Lightweight wrapper around a rule frontmatter dict."""

    def __init__(self, fm: dict[str, Any], source_path: Path):
        self.fm = fm
        self.source_path = source_path

    @property
    def id(self) -> str:
        return self.fm["id"]

    @property
    def version(self) -> str:
        return self.fm["rule_version"]

    @property
    def status(self) -> str:
        return self.fm["status"]

    @property
    def domain(self) -> str:
        return self.fm["domain"]

    @property
    def engine(self) -> str:
        return self.fm["engine"]

    @property
    def precedence(self) -> int:
        return int(self.fm["precedence"])

    @property
    def applies_to(self) -> list[str]:
        return list(self.fm.get("applies_to") or [])

    @property
    def body(self) -> dict[str, Any]:
        return dict(self.fm.get("body") or {})

    def __repr__(self) -> str:
        return f"<Rule {self.id} v{self.version} prec={self.precedence}>"


def load_rules(rules_dir: Path) -> dict[str, Rule]:
    """Load all .md files in rules_dir as Rule entities.

    Skips files that are not rules (no type=rule in frontmatter, or no frontmatter).
    """
    if not rules_dir.exists():
        raise RuleLoadError(f"rules_dir does not exist: {rules_dir}")
    if not rules_dir.is_dir():
        raise RuleLoadError(f"rules_dir is not a directory: {rules_dir}")

    registry: dict[str, Rule] = {}
    for path in sorted(rules_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            fm, _body = frontmatter.read(path)
        except Exception as exc:
            raise RuleLoadError(f"failed to parse {path}: {exc}") from exc
        if not fm or fm.get("type") != "rule":
            continue
        # Minimal validation — full schema in P1
        for required in ("id", "rule_version", "status", "domain", "engine",
                         "precedence", "applies_to", "body"):
            if required not in fm:
                raise RuleLoadError(f"{path.name}: rule missing required field {required!r}")
        rule = Rule(fm, path)
        if rule.id in registry:
            raise RuleLoadError(f"duplicate rule id {rule.id!r} ({path} and {registry[rule.id].source_path})")
        registry[rule.id] = rule
    return registry


def filter_rules(
    registry: dict[str, Rule],
    *,
    domain: str | None = None,
    status: str | None = "active",
    engine: str | None = None,
) -> list[Rule]:
    """Filter rules by attributes. Default: only active rules."""
    out: list[Rule] = []
    for rule in registry.values():
        if domain is not None and rule.domain != domain:
            continue
        if status is not None and rule.status != status:
            continue
        if engine is not None and rule.engine != engine:
            continue
        out.append(rule)
    return sorted(out, key=lambda r: -r.precedence)
