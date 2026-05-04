"""Prompt loader.

Loads Prompt entities (Markdown + YAML frontmatter) from a directory and
exposes a registry indexed by id.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import frontmatter


class PromptLoadError(ValueError):
    pass


class Prompt:
    """Lightweight wrapper around a prompt frontmatter dict."""

    def __init__(self, fm: dict[str, Any], source_path: Path):
        self.fm = fm
        self.source_path = source_path

    @property
    def id(self) -> str:
        return self.fm["id"]

    @property
    def version(self) -> str:
        return self.fm["prompt_version"]

    @property
    def status(self) -> str:
        return self.fm["status"]

    @property
    def applies_to(self) -> list[str]:
        return list(self.fm.get("applies_to") or [])

    @property
    def inputs_spec(self) -> list[dict[str, Any]]:
        return list(self.fm.get("inputs") or [])

    @property
    def template(self) -> str:
        return self.fm.get("template") or ""

    @property
    def system_prompt(self) -> str | None:
        return self.fm.get("system_prompt")

    @property
    def output_format(self) -> str:
        return self.fm.get("output_format", "markdown")

    @property
    def output_schema(self) -> dict[str, Any] | None:
        sch = self.fm.get("output_schema")
        return dict(sch) if isinstance(sch, dict) else None

    @property
    def model_hint(self) -> str | None:
        return self.fm.get("model_hint")

    @property
    def temperature_hint(self) -> float | None:
        v = self.fm.get("temperature_hint")
        return float(v) if v is not None else None

    def __repr__(self) -> str:
        return f"<Prompt {self.id} v{self.version}>"


def load_prompts(prompts_dir: Path) -> dict[str, Prompt]:
    """Load all .md prompt entities. Skips README and non-prompt files."""
    if not prompts_dir.exists():
        raise PromptLoadError(f"prompts_dir does not exist: {prompts_dir}")
    if not prompts_dir.is_dir():
        raise PromptLoadError(f"prompts_dir is not a directory: {prompts_dir}")

    registry: dict[str, Prompt] = {}
    for path in sorted(prompts_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            fm, _body = frontmatter.read(path)
        except Exception as exc:
            raise PromptLoadError(f"failed to parse {path}: {exc}") from exc
        if not fm or fm.get("type") != "prompt":
            continue
        for required in ("id", "prompt_version", "status", "applies_to",
                         "inputs", "output_format", "template"):
            if required not in fm:
                raise PromptLoadError(f"{path.name}: prompt missing required field {required!r}")
        prm = Prompt(fm, path)
        if prm.id in registry:
            raise PromptLoadError(f"duplicate prompt id {prm.id!r}")
        registry[prm.id] = prm
    return registry
