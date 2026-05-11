from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import frontmatter
from shared.obsidian_staging import classify_material, create_staging_note


def test_classifies_yulu_design_methodology_as_pattern_candidate() -> None:
    result = classify_material(
        "御炉门头品牌升级案例：用场景动线、识别符号和餐饮运营节奏沉淀一套设计方法论。"
    )

    assert result.material_type == "brand_case"
    assert result.project == "yulu"
    assert result.asset_type == "brand_reference"
    assert "project/yulu" in result.tags


def test_yulu_related_keywords_set_brand_reference() -> None:
    for text in ["烤鸭出品结构观察", "北京餐饮老字号空间更新", "非遗技艺与门店体验"]:
        result = classify_material(text)
        assert result.project == "yulu"
        assert result.asset_type == "brand_reference"


def test_classifies_github_repository_as_tool_reference() -> None:
    result = classify_material("https://github.com/zarazhangrui/beautiful-html-templates")

    assert result.material_type == "github_tool"
    assert result.asset_type == "reference"
    assert "github-tool" in result.tags


def test_classifies_design_reference_and_image_asset() -> None:
    design = classify_material("一组关于版式、配色和字体层级的设计参考。")
    image = classify_material("图片说明：暗色 AI 工作台主视觉，适合做小红书封面背景。")

    assert design.material_type == "design_reference"
    assert "design-reference" in design.tags
    assert image.material_type == "image_asset"
    assert "image-asset" in image.tags


def test_prompt_keywords_set_prompt_candidate() -> None:
    for text in ["Midjourney 生图提示词", "Lovart 品牌提案 prompt", "提示词模板"]:
        result = classify_material(text)
        assert result.asset_type == "prompt_candidate"


def test_create_staging_note_writes_obsidian_markdown_with_frontmatter(tmp_path: Path) -> None:
    note_path = create_staging_note(
        content="一套关于餐饮翻台、门店动线、菜单结构的运营观察。",
        out_dir=tmp_path / "00_Inbox_Staging",
        title="餐饮运营观察",
        source="manual-note",
        dry_run=True,
    )

    assert note_path.parent.name == "00_Inbox_Staging"
    assert note_path.exists()

    fm, body = frontmatter.read(note_path)
    assert fm["title"] == "餐饮运营观察"
    assert "captured_at" in fm
    assert "project" in fm
    assert fm["material_type"] == "restaurant_ops"
    assert fm["asset_type"] == "reference"
    assert fm["source"] == "manual-note"
    assert fm["dry_run"] is True
    assert "餐饮运营观察" in body
    assert "一套关于餐饮翻台" in body


def test_wechat_source_creates_note_with_required_frontmatter(tmp_path: Path) -> None:
    note_path = create_staging_note(
        content="https://mp.weixin.qq.com/s/example",
        out_dir=tmp_path / "00_Inbox_Staging",
        title="微信文章标题",
        source="wechat",
        dry_run=True,
    )

    fm, body = frontmatter.read(note_path)
    assert fm["title"] == "微信文章标题"
    assert fm["source"] == "wechat"
    assert fm["status"] == "inbox"
    assert "captured_at" in fm
    assert "project" in fm
    assert "asset_type" in fm
    assert "tags" in fm
    assert "微信文章标题" in body


def test_cli_dry_run_creates_note_in_requested_staging_dir(tmp_path: Path) -> None:
    out_dir = tmp_path / "00_Inbox_Staging"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "obsidian_capture.py"),
            "--input",
            "Prompt 模板：让 Codex 先分析资料，再生成品牌提案结构。",
            "--title",
            "Codex 品牌提案 Prompt",
            "--source",
            "chat",
            "--out",
            str(out_dir),
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "dry_run=True" in result.stdout
    created = sorted(out_dir.glob("*.md"))
    assert len(created) == 1
    fm, _ = frontmatter.read(created[0])
    assert fm["material_type"] == "prompt"
    assert fm["asset_type"] == "prompt_candidate"


def test_capture_shortcut_creates_wechat_note_in_default_staging_dir() -> None:
    title = "快捷入口微信测试"
    result = subprocess.run(
        [
            str(ROOT / "scripts" / "capture.sh"),
            "wechat",
            title,
            "这是一篇关于北京老字号升级的微信文章",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    created_note: Path | None = None

    try:
        assert result.returncode == 0, result.stderr
        assert "dry_run=False" in result.stdout
        created = sorted((ROOT / "00_Inbox_Staging").glob("*.md"), key=lambda p: p.stat().st_mtime)
        assert created
        created_note = created[-1]
        fm, body = frontmatter.read(created_note)
        assert fm["title"] == title
        assert fm["source"] == "wechat"
        assert fm["project"] == "yulu"
        assert fm["asset_type"] == "brand_reference"
        assert fm["dry_run"] is False
        assert "北京老字号升级" in body
    finally:
        if created_note and created_note.exists():
            created_note.unlink()


def test_capture_shortcut_explicit_dry_run_marks_wechat_note() -> None:
    title = "快捷入口微信预演测试"
    result = subprocess.run(
        [
            str(ROOT / "scripts" / "capture.sh"),
            "--dry-run",
            "wechat",
            title,
            "这是一篇关于北京老字号升级的微信文章",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    created_note: Path | None = None

    try:
        assert result.returncode == 0, result.stderr
        assert "dry_run=True" in result.stdout
        created = sorted((ROOT / "00_Inbox_Staging").glob("*.md"), key=lambda p: p.stat().st_mtime)
        assert created
        created_note = created[-1]
        fm, body = frontmatter.read(created_note)
        assert fm["title"] == title
        assert fm["source"] == "wechat"
        assert fm["project"] == "yulu"
        assert fm["asset_type"] == "brand_reference"
        assert fm["dry_run"] is True
        assert "北京老字号升级" in body
    finally:
        if created_note and created_note.exists():
            created_note.unlink()
