# 资料自动沉淀到 Obsidian：Staging 工作流

这个工作流把链接、图片说明、文章正文或 GitHub 仓库地址，先沉淀为标准 Obsidian Markdown 文件。

当前版本是本地 staging：

- 不联网；
- 不调用真实 API；
- 不抓取网页正文；
- 只基于输入文本和来源字符串做规则分类；
- 默认输出到仓库根目录 `00_Inbox_Staging/`；
- 默认生成正式 staging 笔记，`dry_run: false`；
- 只有显式传入 `--dry-run` 时，才标记为 `dry_run: true`。

## 目标

输入一条资料后，自动生成带 YAML frontmatter 的 Markdown note，供后续人工整理到 Obsidian vault。

支持资料类型：

- `brand_case`：品牌案例；
- `design_reference`：设计参考；
- `restaurant_ops`：餐饮运营；
- `github_tool`：GitHub 工具；
- `prompt`：提示词；
- `image_asset`：图片资产。

特殊规则：

- 如果内容包含 `御炉`、`御爐`、`yulu`、`烤鸭`、`北京`、`非遗`、`老字号`，自动写入 `project: yulu` 和 `asset_type: brand_reference`。
- 如果内容包含 `提示词`、`prompt`、`Midjourney`、`Lovart`、`生图`，自动写入 `asset_type: prompt_candidate`。
- 如果内容包含设计方法论、流程、工作流、判断标准、沉淀、先分析、提案结构等信号，自动写入 `asset_type: pattern_candidate`。

## 使用方式

```bash
python3 scripts/obsidian_capture.py \
  --input "https://github.com/zarazhangrui/beautiful-html-templates" \
  --title "Beautiful HTML Templates" \
  --source "github"
```

默认输出到：

```text
00_Inbox_Staging/
```

也可以指定输出目录：

```bash
python3 scripts/obsidian_capture.py \
  --input "御炉门头品牌升级案例：沉淀一套餐饮品牌设计方法论。" \
  --title "御炉品牌方法论素材" \
  --source "manual-note" \
  --out 00_Inbox_Staging
```

## 微信资料如何进入当前仓库

当前版本不调用微信接口，也不抓取公众号正文。微信资料进入仓库有两种方式：

1. 复制微信文章链接，作为 `--input` 输入。
2. 复制微信文章正文或摘要，作为 `--input` 输入。

来源统一标记为：

```bash
--source "wechat"
```

日常快捷命令：

```bash
./scripts/capture.sh wechat "文章标题" "文章内容或链接"
```

示例：

```bash
./scripts/capture.sh wechat "北京老字号案例" "这是一篇关于北京老字号升级的微信文章"
```

快捷命令内部仍然调用 `scripts/obsidian_capture.py`，默认写入 `00_Inbox_Staging/`，并生成正式 staging 笔记。

如果只想预演并明确标记，可以显式传入 `--dry-run`：

```bash
./scripts/capture.sh --dry-run wechat "北京老字号案例" "这是一篇关于北京老字号升级的微信文章"
```

原 Python 命令仍然可用，适合需要显式指定参数或扩展后续选项时使用：

```bash
python3 scripts/obsidian_capture.py \
  --input "微信文章内容或链接" \
  --title "文章标题" \
  --source "wechat" \
  --out 00_Inbox_Staging
```

如果微信内容里包含御炉、烤鸭、北京、非遗、老字号等关键词，会进入 `project: yulu`，并标记为 `asset_type: brand_reference`。

如果微信内容是提示词、生图方法、Midjourney 或 Lovart 工作流，会标记为 `asset_type: prompt_candidate`。

## 输出结构

生成文件形如：

```markdown
---
title: 御炉品牌方法论素材
captured_at: '2026-05-10T00:00:00Z'
created_at: '2026-05-10T00:00:00Z'
status: inbox
material_type: brand_case
asset_type: brand_reference
source: manual-note
dry_run: false
tags:
- brand-case
- brand-reference
- project/yulu
project: yulu
---
# 御炉品牌方法论素材

## 自动判断

- 资料类型：brand_case
- 资产类型：pattern_candidate
- 项目：yulu
```

## 文件职责

- `scripts/obsidian_capture.py`：命令行入口，默认生成正式 staging 笔记，可用 `--dry-run` 标记预演。
- `shared/obsidian_staging.py`：分类、frontmatter、文件名和 Markdown 生成逻辑。
- `tests/test_obsidian_staging.py`：本地 staging 行为测试。
- `examples/obsidian_staging/`：示例输入。
- `00_Inbox_Staging/`：默认输出目录。

## 验证命令

```bash
python3 -m pytest tests/test_obsidian_staging.py -q

python3 scripts/obsidian_capture.py \
  --input "Prompt 模板：让 Codex 先分析资料，再生成品牌提案结构。" \
  --title "Codex 品牌提案 Prompt" \
  --source "chat" \
  --out 00_Inbox_Staging
```

## 后续扩展

当前版本只做本地 staging。后续可以扩展：

- URL 正文抓取；
- 图片 OCR；
- GitHub README 自动读取；
- Obsidian vault 目录路由；
- 根据 frontmatter 自动移动到项目目录或 pattern 候选库。
