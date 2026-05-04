"""Prompt rendering helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from string import Formatter
from typing import Any

from .prompt_loader import Prompt


class RenderError(ValueError):
    pass


@dataclass
class RenderedPrompt:
    prompt_id: str
    prompt_version: str
    system: str
    user: str
    model_hint: str
    temperature_hint: float | None
    output_format: str
    output_schema: dict[str, Any]
    declared_inputs: dict[str, Any]
    inputs_hash: str


class _FormatMap(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render_template(template: str, context: dict[str, Any]) -> str:
    mapping = _FormatMap()
    for key, value in context.items():
        if isinstance(value, (dict, list)):
            mapping[key] = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            mapping[key] = str(value)
    try:
        return Formatter().vformat(template, (), mapping)
    except Exception as exc:
        raise RenderError(f"failed to render prompt template: {exc}") from exc


def render(prompt: Prompt, context: dict[str, Any]) -> RenderedPrompt:
    payload = json.dumps(context, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return RenderedPrompt(
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        system=_render_template(prompt.system, context),
        user=_render_template(prompt.user_template, context),
        model_hint=prompt.model_hint,
        temperature_hint=prompt.temperature_hint,
        output_format=prompt.output_format,
        output_schema=prompt.output_schema,
        declared_inputs=context,
        inputs_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )

