from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from shared import frontmatter


MATERIAL_TYPES = {
    "brand_case",
    "design_reference",
    "restaurant_ops",
    "github_tool",
    "prompt",
    "image_asset",
}

YULU_KEYWORDS = ["御炉", "御爐", "yulu", "御炉餐饮", "御爐餐飲", "烤鸭", "北京", "非遗", "老字号"]
PROMPT_KEYWORDS = ["prompt", "提示词", "system prompt", "指令", "midjourney", "lovart", "生图"]
METHODOLOGY_KEYWORDS = [
    "方法论",
    "方法論",
    "框架",
    "流程",
    "工作流",
    "设计原则",
    "設計原則",
    "判断标准",
    "沉淀",
    "先分析",
    "提案结构",
]


@dataclass(frozen=True)
class Classification:
    material_type: str
    asset_type: str
    project: str | None
    tags: list[str]


def classify_material(content: str, source: str = "") -> Classification:
    text = f"{content}\n{source}".lower()
    raw = f"{content}\n{source}"

    material_type = _material_type(text, raw)
    tags = [_tag_for_material(material_type)]

    is_yulu = _contains_any(raw, YULU_KEYWORDS)
    is_prompt = _contains_any(raw, PROMPT_KEYWORDS)
    project = "yulu" if is_yulu else None

    is_methodology = _contains_any(raw, METHODOLOGY_KEYWORDS)
    if is_prompt:
        asset_type = "prompt_candidate"
    elif is_yulu:
        asset_type = "brand_reference"
    elif is_methodology:
        asset_type = "pattern_candidate"
    else:
        asset_type = "reference"
    if asset_type == "pattern_candidate":
        tags.append("design-methodology")
    if asset_type == "brand_reference":
        tags.append("brand-reference")
    if asset_type == "prompt_candidate":
        tags.append("prompt-candidate")
    if project:
        tags.append(f"project/{project}")

    return Classification(
        material_type=material_type,
        asset_type=asset_type,
        project=project,
        tags=tags,
    )


def create_staging_note(
    *,
    content: str,
    out_dir: Path,
    title: str | None = None,
    source: str = "",
    dry_run: bool = False,
    now: datetime | None = None,
) -> Path:
    timestamp = now or datetime.now(timezone.utc)
    title = title or infer_title(content, source)
    classification = classify_material(content, source)
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp.strftime('%Y%m%d-%H%M%S')}-{slugify(title, content)}.md"
    note_path = out_dir / filename
    if note_path.exists():
        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:8]
        note_path = out_dir / f"{timestamp.strftime('%Y%m%d-%H%M%S')}-{slugify(title, content)}-{digest}.md"

    fm: dict[str, object] = {
        "title": title,
        "captured_at": timestamp.isoformat().replace("+00:00", "Z"),
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "status": "inbox",
        "material_type": classification.material_type,
        "asset_type": classification.asset_type,
        "source": source or "manual",
        "project": classification.project,
        "dry_run": dry_run,
        "tags": classification.tags,
    }

    body = render_body(title=title, content=content, classification=classification)
    frontmatter.write(note_path, fm, body)
    return note_path


def infer_title(content: str, source: str = "") -> str:
    if source.startswith("http"):
        return source.rstrip("/").split("/")[-1] or "未命名资料"
    first_line = next((line.strip() for line in content.splitlines() if line.strip()), "")
    if not first_line:
        return "未命名资料"
    return first_line[:36]


def render_body(*, title: str, content: str, classification: Classification) -> str:
    project_line = f"- 项目：{classification.project}\n" if classification.project else ""
    return (
        f"# {title}\n\n"
        "## 自动判断\n\n"
        f"- 资料类型：{classification.material_type}\n"
        f"- 资产类型：{classification.asset_type}\n"
        f"{project_line}"
        f"- 标签：{', '.join(classification.tags)}\n\n"
        "## 原始资料\n\n"
        f"{content.strip()}\n\n"
        "## 后续处理建议\n\n"
        "- 人工确认分类是否正确。\n"
        "- 如果值得复用，补充判断过程、适用场景和反例。\n"
        "- 如果只是临时资料，处理后从 Inbox 移走或删除。\n"
    )


def slugify(title: str, fallback_text: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if ascii_slug:
        return ascii_slug[:60]
    digest = hashlib.sha1(fallback_text.encode("utf-8")).hexdigest()[:10]
    return f"note-{digest}"


def _material_type(text: str, raw: str) -> str:
    if "github.com/" in text or re.search(r"\b(repo|repository|cli|sdk|framework|library)\b", text):
        return "github_tool"
    if _contains_any(raw, PROMPT_KEYWORDS):
        return "prompt"
    if _contains_any(raw, ["图片", "图像", "主视觉", "海报", "照片", "image", "png", "jpg", "jpeg"]):
        return "image_asset"
    if _contains_any(raw, ["品牌", "案例", "定位", "提案", "视觉识别", "logo", "slogan"]):
        return "brand_case"
    if _contains_any(raw, ["餐饮", "门店", "翻台", "菜单", "客单", "后厨", "运营", "外卖"]):
        return "restaurant_ops"
    if _contains_any(raw, ["设计", "版式", "配色", "字体", "参考", "模板", "layout"]):
        return "design_reference"
    return "design_reference"


def _tag_for_material(material_type: str) -> str:
    return material_type.replace("_", "-")


def _contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)
