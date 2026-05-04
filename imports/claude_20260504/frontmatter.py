"""YAML frontmatter parser/writer (PyYAML-backed).

API (preserved from hand-written version):
    frontmatter.read(path) -> (dict, body_str)
    frontmatter.write(path, dict, body_str) -> None
    frontmatter.dump(dict) -> str
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def read(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = _FM_RE.match(text)
    if not match:
        return {}, text
    fm_text = match.group(1)
    body = text[match.end():]
    if not fm_text.strip():
        return {}, body
    try:
        loaded = yaml.load(fm_text, Loader=_StringPreservingLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"frontmatter YAML parse error in {path}: {exc}") from exc
    if loaded is None:
        return {}, body
    if not isinstance(loaded, dict):
        raise ValueError(f"frontmatter in {path} must be a mapping, got {type(loaded).__name__}")
    return loaded, body


class _OrderedSafeDumper(yaml.SafeDumper):
    pass


# Make safe_load NOT auto-convert ISO dates / datetimes to date objects.
# We want all timestamps to stay as strings for clean JSON serialization.
class _StringPreservingLoader(yaml.SafeLoader):
    pass


def _date_as_string_constructor(loader, node):
    return loader.construct_scalar(node)


_StringPreservingLoader.add_constructor("tag:yaml.org,2002:timestamp", _date_as_string_constructor)


def _dict_representer(dumper, data):
    return dumper.represent_dict(data.items())


def _str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_OrderedSafeDumper.add_representer(dict, _dict_representer)
_OrderedSafeDumper.add_representer(str, _str_representer)


def dump(obj: dict[str, Any]) -> str:
    return yaml.dump(
        obj,
        Dumper=_OrderedSafeDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def write(path: Path, frontmatter: dict[str, Any], body: str = "") -> None:
    content = "---\n" + dump(frontmatter) + "---\n" + body
    path.write_text(content, encoding="utf-8")
