"""Prompt entity loader."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import frontmatter


class PromptLoadError(ValueError):
    pass


@dataclass
class Prompt:
    id: str
    version: str
    system: str
    user_template: str
    model_hint: str = ""
    temperature_hint: float | None = None
    output_format: str = "json"
    output_schema: dict[str, Any] = field(default_factory=dict)


_SNAPSHOT_RE = re.compile(
    r"# Prompt snapshot — (?P<id>\S+) v(?P<version>\S+).*?--- SYSTEM ---\n(?P<system>.*?)\n--- USER ---\n(?P<user>.*)",
    re.DOTALL,
)


def _prompt_from_path(path: Path) -> Prompt | None:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        fm, body = frontmatter.read(path)
        if fm.get("type") not in {"prompt", "rendered_prompt"}:
            return None
        prompt_id = fm.get("id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise PromptLoadError(f"prompt {path} is missing string id")
        return Prompt(
            id=prompt_id,
            version=str(fm.get("prompt_version") or fm.get("version") or "1.0.0"),
            system=str(fm.get("system") or ""),
            user_template=str(fm.get("user_template") or fm.get("user") or body),
            model_hint=str(fm.get("model_hint") or ""),
            temperature_hint=fm.get("temperature_hint"),
            output_format=str(fm.get("output_format") or "json"),
            output_schema=fm.get("output_schema") or {},
        )

    match = _SNAPSHOT_RE.match(text)
    if match:
        return Prompt(
            id=match.group("id"),
            version=match.group("version"),
            system=match.group("system").strip(),
            user_template=match.group("user").strip(),
        )
    return None


def load_prompts(root: Path) -> dict[str, Prompt]:
    if not root.exists():
        raise PromptLoadError(f"prompts directory does not exist: {root}")
    paths = [root] if root.is_file() else sorted(root.rglob("*"))
    prompts: dict[str, Prompt] = {}
    for path in paths:
        if not path.is_file() or path.suffix not in {".md", ".txt", ""}:
            continue
        prompt = _prompt_from_path(path)
        if prompt is None:
            continue
        prompts[prompt.id] = prompt
    return prompts

