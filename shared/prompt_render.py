"""Prompt rendering.

Implements the render_prompt(prompt_id, context) contract from
references/schemas/04_prompt.md.

Behavior:
  - Validates required inputs are present
  - Type-checks declared inputs (best-effort, common types only)
  - Renders {{var}} placeholders into the template
  - Renders synthesized {{*_block}} variables (formatted multi-line blocks)
  - Returns a RenderedPrompt with system / user / metadata
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from .prompt_loader import Prompt


PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class RenderError(ValueError):
    pass


class MissingInputError(RenderError):
    pass


class InputTypeError(RenderError):
    pass


@dataclass
class RenderedPrompt:
    """Output of render_prompt(). Used by both dry-run and live LLM calls."""
    system: str | None
    user: str
    model_hint: str | None
    temperature_hint: float | None
    output_format: str
    output_schema: dict[str, Any] | None
    prompt_id: str
    prompt_version: str
    inputs_hash: str
    declared_inputs: dict[str, Any]  # what we passed in (after defaults)
    rendered_blocks: dict[str, str] = field(default_factory=dict)  # synthesized blocks


# ---------------------------------------------------------------------------
# Block synthesizers — turn structured inputs into formatted text blocks
# ---------------------------------------------------------------------------

def _block_critique_summary(c: dict[str, Any]) -> str:
    if not c:
        return "(无)"
    lines = [
        f"- weighted_score: {c.get('weighted_score', '?')}",
        f"- decision: {c.get('decision', '?')}",
    ]
    scores = c.get("scores") or []
    if scores:
        lines.append("- 各维度得分:")
        for s in scores:
            lines.append(
                f"  - {s.get('label', s.get('dimension_id', '?'))}: "
                f"{s.get('score', '?')}/5"
            )
    strengths = c.get("strengths") or []
    if strengths:
        lines.append(f"- strengths: {'; '.join(strengths[:3])}")
    return "\n".join(lines)


def _block_existing_patterns(items: list[dict[str, Any]]) -> str:
    if not items:
        return "(空，本次为首个 Pattern)"
    lines = []
    for p in items[:20]:
        lines.append(f"- [{p.get('id', '?')}] {p.get('title', '')} (category={p.get('category', '?')})")
    if len(items) > 20:
        lines.append(f"... 还有 {len(items) - 20} 项")
    return "\n".join(lines)


def _block_evidence_assets(items: list[dict[str, Any]]) -> str:
    if not items:
        return "(无)"
    lines = []
    for a in items[:15]:
        lines.append(
            f"- [{a.get('id', '?')}] {a.get('name', '?')} (category={a.get('category', '?')})"
        )
    if len(items) > 15:
        lines.append(f"... 还有 {len(items) - 15} 项")
    return "\n".join(lines)


def _block_direction(d: dict[str, Any]) -> str:
    if not d:
        return "(无)"
    lines = [
        f"- id: {d.get('id', '?')}",
        f"- name: {d.get('name', '?')}",
        f"- core_idea: {d.get('core_idea', '')}",
        f"- visual_approach: {d.get('visual_approach', '')}",
        f"- rationale: {d.get('rationale', '')}",
    ]
    refs_p = d.get("referenced_patterns") or []
    if refs_p:
        lines.append(f"- referenced_patterns: {', '.join(refs_p)}")
    refs_a = d.get("referenced_assets") or []
    if refs_a:
        lines.append(f"- referenced_assets: {', '.join(refs_a)}")
    return "\n".join(lines)


def _block_peer_directions(items: list[dict[str, Any]]) -> str:
    if not items:
        return "(无其他方向用于对比)"
    lines = []
    for d in items:
        name = d.get("name", "?")
        idea = d.get("core_idea", "")
        lines.append(f"- [{d.get('id', '?')}] {name}: {idea}")
    return "\n".join(lines)


def _block_rubric(rubric: dict[str, Any]) -> str:
    if not rubric:
        return "(无 rubric)"
    dimensions = rubric.get("dimensions") or []
    lines = ["维度（id | label | weight | 定义）:"]
    for dim in dimensions:
        lines.append(
            f"- {dim.get('id', '?')} | {dim.get('label', '')} "
            f"| {dim.get('weight', 0)} | {dim.get('definition', '')}"
        )
    scale = rubric.get("scale") or [1, 5]
    lines.append(f"\n评分量表: {scale[0]}-{scale[1]} 整数")
    anchors = rubric.get("scale_anchors") or {}
    if anchors:
        lines.append("锚点:")
        for k in sorted(anchors):
            lines.append(f"  {k}: {anchors[k]}")
    return "\n".join(lines)


def _block_deliverables(items: list[dict[str, Any]]) -> str:
    if not items:
        return "(无)"
    lines = []
    for d in items:
        name = d.get("name", "?")
        cat = d.get("category", "?")
        qty = d.get("qty", "?")
        lines.append(f"- {name} ({cat}, ×{qty})")
    return "\n".join(lines)


def _block_asset_summaries(items: list[dict[str, Any]]) -> str:
    if not items:
        return "(无)"
    lines = []
    for a in items[:30]:  # 截断防止 prompt 过长
        aid = a.get("id", "?")
        cat = a.get("category", "?")
        name = a.get("name", "?")
        role = a.get("family_role") or "-"
        lines.append(f"- [{aid}][{cat}/{role}] {name}")
    if len(items) > 30:
        lines.append(f"... 还有 {len(items) - 30} 项")
    return "\n".join(lines)


def _block_string_list(items: list[Any]) -> str:
    if not items:
        return "(无)"
    return "\n".join(f"- {item}" for item in items)


def _block_must_avoid(items: list[Any]) -> str:
    if not items:
        return "(无特殊禁忌)"
    return ", ".join(str(item) for item in items)


# ---------------------------------------------------------------------------
# Type coercion / check
# ---------------------------------------------------------------------------

_TYPE_VALIDATORS = {
    "string": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list),
    "dict": lambda v: isinstance(v, dict),
}


def _validate_input_type(name: str, value: Any, type_spec: str, enum: list[Any] | None) -> None:
    # Strip "list[xxx]" — we only check outer container
    base = type_spec.split("[", 1)[0].strip()
    if base == "enum":
        if enum is not None and value not in enum:
            raise InputTypeError(f"input {name!r}: value {value!r} not in enum {enum}")
        return
    validator = _TYPE_VALIDATORS.get(base)
    if validator is None:
        # Unknown type — best-effort skip
        return
    if not validator(value):
        raise InputTypeError(f"input {name!r}: expected {type_spec}, got {type(value).__name__}")


# ---------------------------------------------------------------------------
# Public: render
# ---------------------------------------------------------------------------

def render(prompt: Prompt, context: dict[str, Any]) -> RenderedPrompt:
    """Render a Prompt entity with a context dict.

    Mirrors the contract in references/schemas/04_prompt.md §"渲染契约".
    """
    if prompt.status != "active":
        raise RenderError(f"prompt {prompt.id!r} status is {prompt.status!r}, must be 'active'")

    # 1. Resolve declared_inputs — apply defaults, validate required, type-check
    declared: dict[str, Any] = {}
    for spec in prompt.inputs_spec:
        name = spec["name"]
        type_spec = spec.get("type", "string")
        enum = spec.get("enum")
        required = bool(spec.get("required", False))
        default = spec.get("default")

        if name in context and context[name] is not None:
            value = context[name]
        elif required:
            raise MissingInputError(f"prompt {prompt.id!r}: missing required input {name!r}")
        else:
            value = default if default is not None else _default_for_type(type_spec)
        _validate_input_type(name, value, type_spec, enum)
        declared[name] = value

    # 2. Synthesize blocks from declared inputs
    blocks = _synthesize_blocks(declared)

    # 3. Render template
    rendered_user = _render_template(prompt.template, declared, blocks)

    # 4. Compute inputs_hash (canonical JSON of declared inputs)
    payload = json.dumps(declared, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    inputs_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return RenderedPrompt(
        system=prompt.system_prompt,
        user=rendered_user,
        model_hint=prompt.model_hint,
        temperature_hint=prompt.temperature_hint,
        output_format=prompt.output_format,
        output_schema=prompt.output_schema,
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        inputs_hash=inputs_hash,
        declared_inputs=declared,
        rendered_blocks=blocks,
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _default_for_type(type_spec: str) -> Any:
    base = type_spec.split("[", 1)[0].strip()
    return {
        "string": "",
        "int": 0,
        "float": 0.0,
        "bool": False,
        "list": [],
        "dict": {},
        "enum": None,
    }.get(base, None)


def _synthesize_blocks(inputs: dict[str, Any]) -> dict[str, str]:
    """Build the formatted *_block variables that prm_run_concept references."""
    blocks: dict[str, str] = {}

    if "deliverables" in inputs:
        blocks["deliverables_block"] = _block_deliverables(inputs["deliverables"])
    if "asset_summaries" in inputs:
        blocks["asset_summaries_block"] = _block_asset_summaries(inputs["asset_summaries"])
    if "pattern_refs" in inputs:
        blocks["pattern_refs_block"] = _block_string_list(inputs["pattern_refs"])
    if "open_questions" in inputs:
        blocks["open_questions_block"] = _block_string_list(inputs["open_questions"])
    if "must_avoid" in inputs:
        blocks["must_avoid_block"] = _block_must_avoid(inputs["must_avoid"])
    # critic-specific blocks
    if "direction" in inputs:
        blocks["direction_block"] = _block_direction(inputs["direction"])
    if "peer_directions" in inputs:
        blocks["peer_directions_block"] = _block_peer_directions(inputs["peer_directions"])
    if "rubric" in inputs:
        blocks["rubric_block"] = _block_rubric(inputs["rubric"])
    # archive-specific blocks
    if "critique_summary" in inputs:
        blocks["critique_summary_block"] = _block_critique_summary(inputs["critique_summary"])
    if "existing_patterns" in inputs:
        blocks["existing_patterns_block"] = _block_existing_patterns(inputs["existing_patterns"])
    if "evidence_assets" in inputs:
        blocks["evidence_assets_block"] = _block_evidence_assets(inputs["evidence_assets"])

    # tone_override has a "_or_default" sibling
    tone = inputs.get("tone_override") or ""
    blocks["tone_override_or_default"] = tone if tone else "(项目默认调性)"

    return blocks


def _render_template(template: str, inputs: dict[str, Any], blocks: dict[str, str]) -> str:
    """Replace {{var}} occurrences with values from inputs ∪ blocks."""
    merged: dict[str, Any] = {**inputs, **blocks}

    def _replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in merged:
            # Leave intact and warn — caller should have errored at validate stage
            return match.group(0)
        value = merged[name]
        if value is None:
            return ""
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    return PLACEHOLDER_RE.sub(_replace, template)
